from enum import StrEnum


class TributeRequestType(StrEnum):
    NEW_DIGITAL_PRODUCT = 'new_digital_product'
    PHYSICAL_ORDER_CANCELED = 'physical_order_canceled'
    PHYSICAL_ORDER_SHIPPED = 'physical_order_shipped'
    PHYSICAL_ORDER_CREATED = 'physical_order_created'
    CANCELLED_SUBSCRIPTION = 'cancelled_subscription'
    NEW_SUBSCRIPTION = 'new_subscription'
    NEW_DONATION = 'new_donation'
    RECURRENT_DONATION = 'recurrent_donation'
    CANCELLED_DONATION = 'cancelled_donation'
    SHOP_ORDER = 'shop_order'
