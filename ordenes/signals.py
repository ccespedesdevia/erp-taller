from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import RepuestoUsado
from inventario.models import MovimientoStock


@receiver(pre_save, sender=RepuestoUsado)
def track_old_quantity(sender, instance, **kwargs):
    if instance.pk:
        instance._old_quantity = RepuestoUsado.objects.get(pk=instance.pk).cantidad
    else:
        instance._old_quantity = 0


@receiver(post_save, sender=RepuestoUsado)
def descontar_stock(sender, instance, **kwargs):
    old_qty = getattr(instance, '_old_quantity', 0)
    delta = instance.cantidad - old_qty
    if delta != 0:
        instance.producto.stock_actual -= delta
        instance.producto.save(update_fields=['stock_actual'])
        MovimientoStock.objects.create(
            producto=instance.producto,
            tipo='salida',
            cantidad=abs(delta),
            referencia=f'OS #{instance.orden.id}',
        )


@receiver(post_delete, sender=RepuestoUsado)
def reponer_stock(sender, instance, **kwargs):
    instance.producto.stock_actual += instance.cantidad
    instance.producto.save(update_fields=['stock_actual'])
