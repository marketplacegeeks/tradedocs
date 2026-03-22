import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradetocs.settings')
django.setup()

from apps.accounts.models import User

u = User.objects.get(email='mehareac@gmail.com')
u.set_password('V@nita@24')
u.role = 'COMPANY_ADMIN'
u.is_staff = True
u.is_superuser = True
u.save()
print('Password reset done for:', u.email)
