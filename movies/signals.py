from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    """Associe l'utilisateur au groupe Django correspondant a son role."""
    if created:
        # Les groupes facilitent la gestion des permissions depuis l'administration.
        if instance.role == User.Role.ADMIN:
            admin_group, _ = Group.objects.get_or_create(name='Administrators')
            instance.groups.add(admin_group)
        else:
            spectator_group, _ = Group.objects.get_or_create(name='Spectators')
            instance.groups.add(spectator_group)
