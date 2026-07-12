import { test, expect, Page } from '@playwright/test';
import xlsxPkg from 'xlsx';
const { readFile, utils } = xlsxPkg;
import path from 'path';

// Path to the filled-in Excel file. Override with:
//   ORG_FIXTURE=/path/to/your.xlsx npm --prefix frontend run e2e
const FIXTURE_PATH = process.env.ORG_FIXTURE
  ? path.resolve(process.env.ORG_FIXTURE)
  : path.resolve(__dirname, 'fixtures/organisations.xlsx');

const LOGIN_EMAIL = process.env.E2E_EMAIL ?? 'mehareac@gmail.com';
const LOGIN_PASSWORD = process.env.E2E_PASSWORD ?? 'V@nita@24';

interface OrgRow {
  name: string;
  tags: string[];
}

interface AddressRow {
  addressType: string;
  line1: string;
  line2: string;
  city: string;
  state: string;
  pin: string;
  country: string;
  email: string;
  contactName: string;
  phoneCountryCode: string;
  phoneNumber: string;
  iecCode: string;
  taxType: string;
  taxCode: string;
}

// Excel auto-formats dial code columns as plain numbers (91, not "+91"). The backend's
// phone validator does raw string concatenation (code + number) and needs E.164 format,
// so a missing "+" silently breaks validation. Normalize it here rather than requiring
// the sheet to be typed a specific way.
function normalizeDialCode(value: unknown): string {
  const raw = String(value ?? '').trim();
  if (!raw) return '';
  return raw.startsWith('+') ? raw : `+${raw}`;
}

function loadFixture(): { orgs: OrgRow[]; addressesByOrg: Map<string, AddressRow[]> } {
  const wb = readFile(FIXTURE_PATH);

  const orgSheet = utils.sheet_to_json<Record<string, unknown>>(wb.Sheets['Organisations'], {
    range: 1,
    header: ['name', 'tags'],
  });
  const addrSheet = utils.sheet_to_json<Record<string, unknown>>(wb.Sheets['Addresses'], {
    range: 1,
    header: [
      'orgName', 'addressType', 'line1', 'line2', 'city', 'state', 'pin', 'country',
      'email', 'contactName', 'phoneCountryCode', 'phoneNumber', 'iecCode', 'taxType', 'taxCode',
    ],
  });

  const orgs: OrgRow[] = orgSheet
    .filter((r) => r.name && String(r.name).trim())
    .map((r) => ({
      name: String(r.name).trim(),
      tags: String(r.tags ?? '').split(',').map((t) => t.trim()).filter(Boolean),
    }));

  const addressesByOrg = new Map<string, AddressRow[]>();
  addrSheet
    .filter((r) => r.orgName && String(r.orgName).trim())
    .forEach((r) => {
      const key = String(r.orgName).trim();
      const list = addressesByOrg.get(key) ?? [];
      list.push({
        addressType: String(r.addressType ?? '').trim(),
        line1: String(r.line1 ?? ''),
        line2: String(r.line2 ?? ''),
        city: String(r.city ?? ''),
        state: String(r.state ?? ''),
        pin: String(r.pin ?? ''),
        country: String(r.country ?? ''),
        email: String(r.email ?? ''),
        contactName: String(r.contactName ?? ''),
        phoneCountryCode: normalizeDialCode(r.phoneCountryCode),
        phoneNumber: String(r.phoneNumber ?? ''),
        iecCode: String(r.iecCode ?? ''),
        taxType: String(r.taxType ?? ''),
        taxCode: String(r.taxCode ?? ''),
      });
      addressesByOrg.set(key, list);
    });

  return { orgs, addressesByOrg };
}

async function login(page: Page) {
  await page.goto('/login');
  await page.getByRole('textbox', { name: 'you@example.com' }).fill(LOGIN_EMAIL);
  await page.getByRole('textbox', { name: '••••••••' }).fill(LOGIN_PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: 'Master Data' })).toBeVisible();
}

// Ant Design `Select` (showSearch): click to open + focus its search box, type to filter,
// then confirm with Enter. The filtered option row is virtualized and reports width:0
// (never satisfies Playwright's "visible" check even though it's functional), so we wait
// for it to be attached to the DOM rather than visible, then drive selection via keyboard.
async function pickAntdOption(page: Page, selectNth: number, optionText: string) {
  const select = page.locator('.ant-select').nth(selectNth);
  await select.click();
  await page.keyboard.type(optionText);
  await page.getByRole('option', { name: optionText }).first().waitFor({ state: 'attached' });
  await page.keyboard.press('Enter');
}

async function fillAddress(page: Page, index: number, addr: AddressRow) {
  // Each address block renders exactly 2 antd Selects, in this order: Address Type, Country.
  const addressTypeSelectIndex = index * 2;
  const countrySelectIndex = index * 2 + 1;

  await pickAntdOption(page, addressTypeSelectIndex, addr.addressType);

  await page.locator(`input[name="addresses.${index}.line1"]`).fill(addr.line1);
  if (addr.line2) await page.locator(`input[name="addresses.${index}.line2"]`).fill(addr.line2);
  await page.locator(`input[name="addresses.${index}.city"]`).fill(addr.city);
  if (addr.state) await page.locator(`input[name="addresses.${index}.state"]`).fill(addr.state);
  if (addr.pin) await page.locator(`input[name="addresses.${index}.pin"]`).fill(addr.pin);

  await pickAntdOption(page, countrySelectIndex, addr.country);

  if (addr.email) await page.locator(`input[name="addresses.${index}.email"]`).fill(addr.email);
  if (addr.contactName) await page.locator(`input[name="addresses.${index}.contact_name"]`).fill(addr.contactName);
  // Selecting a country auto-fills the dial code. The backend rejects a dial code with no
  // phone number (and vice versa), so: no phone number in the sheet -> clear the auto-fill;
  // an explicit dial code in the sheet -> override the auto-fill.
  const dialCode = page.locator(`input[name="addresses.${index}.phone_country_code"]`);
  if (!addr.phoneNumber) {
    await dialCode.fill('');
  } else if (addr.phoneCountryCode) {
    await dialCode.fill('');
    await dialCode.fill(addr.phoneCountryCode);
  }
  if (addr.phoneNumber) await page.locator(`input[name="addresses.${index}.phone_number"]`).fill(addr.phoneNumber);
  if (addr.iecCode) await page.locator(`input[name="addresses.${index}.iec_code"]`).fill(addr.iecCode);
  if (addr.taxType) await page.locator(`input[name="addresses.${index}.tax_type"]`).fill(addr.taxType);
  if (addr.taxCode) await page.locator(`input[name="addresses.${index}.tax_code"]`).fill(addr.taxCode);
}

async function createOrganisation(page: Page, org: OrgRow, addresses: AddressRow[]) {
  await page.goto('/master-data/organisations/new');

  await page.getByRole('textbox', { name: 'e.g. Sunrise Exports Pvt Ltd' }).fill(org.name);

  for (const tag of org.tags) {
    // The checkbox input is visually hidden (display:none); its wrapping <label> carries
    // the visible text and native label→input association, so click the label text instead.
    await page.locator('label').filter({ hasText: new RegExp(`^${tag}$`) }).click();
  }

  // The form starts with 1 address already present; add more to match the sheet.
  for (let i = 1; i < addresses.length; i++) {
    await page.getByRole('button', { name: 'Add Another Address' }).click();
  }

  for (let i = 0; i < addresses.length; i++) {
    await fillAddress(page, i, addresses[i]);
  }

  await page.getByRole('button', { name: 'Create Organisation' }).click();
  // Don't assert on the success toast — antd auto-dismisses it in ~3s and the exact
  // save latency varies, so the toast can disappear before a fixed-timeout check runs.
  // The onSuccess handler navigates back to the list page, which is a durable signal.
  await page.waitForURL('**/master-data/organisations', { timeout: 15_000 });
}

const { orgs, addressesByOrg } = loadFixture();

// Not .serial: each organisation is independent, so one bad row (e.g. a typo that fails
// validation) shouldn't skip every organisation listed after it in the sheet.
test.describe('Create organisations from Excel fixture', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  for (const org of orgs) {
    test(`create organisation: ${org.name} (${org.tags.join(', ')})`, async ({ page }) => {
      const addresses = addressesByOrg.get(org.name) ?? [];
      expect(addresses.length, `No addresses found in the Addresses sheet for "${org.name}" — check the Organisation Name matches exactly.`).toBeGreaterThan(0);
      await createOrganisation(page, org, addresses);
    });
  }
});
