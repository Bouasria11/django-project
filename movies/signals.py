from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    """Assign user to appropriate group based on role"""
    if created:
        if instance.role == User.Role.ADMIN:
            admin_group, _ = Group.objects.get_or_create(name='Administrators')
            instance.groups.add(admin_group)
        else:
            spectator_group, _ = Group.objects.get_or_create(name='Spectators')
            instance.groups.add(spectator_group)
