# -*- coding: utf-8 -*-

from django.contrib import admin

from models import Badge,BadgeSettings, ProjectBadge, ProjectBadgeToUser
from singleton_models.admin import SingletonModelAdmin

class BadgeAdmin(admin.ModelAdmin):
    fields = ('name','level','icon',)
    list_display = ('name','level')
    
    
class ProjectBadgeAdmin(admin.ModelAdmin):
    fields = ('name','description','project','badge')
    list_display = ('name', 'description')

class BadgeSettingsAdmin(admin.ModelAdmin):
    fields = ('awardLevel','multipleAwards')
    list_display = ('awardLevel','multipleAwards')

class ProjectBadgeToUserAdmin(admin.ModelAdmin):
    list_display = ('projectbadge','user','created')


admin.site.register(Badge, BadgeAdmin)
admin.site.register(BadgeSettings, BadgeSettingsAdmin)
admin.site.register(ProjectBadge, ProjectBadgeAdmin)
admin.site.register(ProjectBadgeToUser, ProjectBadgeToUserAdmin)
