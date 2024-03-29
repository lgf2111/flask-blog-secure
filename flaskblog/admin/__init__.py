from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView

from flask import flash, redirect, url_for
from flask_login import current_user

class HomeAdminView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return current_user.role_id == 2
    
    def inaccessible_callback(self, name, **kwargs):
        flash("You don't have permission to access this page.", "info")
        return redirect(url_for('main.home'))

class AdminMixin:
    def is_accessible(self):
        return current_user.role_id == 2
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.home'))

class AdminView(AdminMixin, ModelView):
    create_template = 'admin/create.html'
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.role_id == 2

admin = Admin(name='Flask Blog', template_mode='bootstrap4', index_view=HomeAdminView(name='Home'))
