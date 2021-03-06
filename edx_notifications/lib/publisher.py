"""
All in-proc API endpoints for acting as a Notification Publisher
"""

import types
from contracts import contract

from django.db.models.query import ValuesListQuerySet

from edx_notifications.channels.channel import get_notification_channel
from edx_notifications.stores.store import notification_store

from edx_notifications.data import (
    NotificationType,
    NotificationMessage,
)

from edx_notifications.renderers.renderer import (
    register_renderer
)


@contract(msg_type=NotificationType)
def register_notification_type(msg_type):
    """
    Registers a new notification type
    """

    # do validation
    msg_type.validate()

    notification_store().save_notification_type(msg_type)

    # also register the Renderer associated with this
    # type, note that the multiple msg types can have
    # the same renderer, but only one entry will
    # get placed in the registry
    register_renderer(msg_type.renderer)


@contract(type_name=basestring)
def get_notification_type(type_name):
    """
    Returns the NotificationType registered by type_name
    """

    return notification_store().get_notification_type(type_name)


def get_all_notification_types():
    """
    Returns all know Notification types
    """

    return notification_store().get_all_notification_types()


@contract(user_id='int,>0', msg=NotificationMessage)
def publish_notification_to_user(user_id, msg):
    """
    This top level API method will publish a notification
    to a user.

    Ultimately this method will look up the user's preference
    to which NotificationChannel to distribute this over.

    ARGS:
        - user_id: An unconstrained identifier to some user identity
        - msg: A NotificationMessage

    RETURNS:
        A new instance of UserNotification that includes any auto-generated
        fields
    """

    # validate the msg, this will raise a ValidationError if there
    # is something malformatted or missing in the NotificationMessage
    msg.validate()

    # get the notification channel associated
    # for this message type as well as this user
    # as users will be able to choose how to
    # receive their notifications per type.
    #
    # This call will never return None, if there is
    # a problem, it will throw an exception
    channel = get_notification_channel(user_id, msg.msg_type)

    user_msg = channel.dispatch_notification_to_user(user_id, msg)

    #
    # Here is where we will tie into the Analytics pipeline
    #

    return user_msg


@contract(msg=NotificationMessage)
def bulk_publish_notification_to_users(user_ids, msg):
    """
    This top level API method will publish a notification
    to a group (potentially large). We have a distinct entry
    point to consider any optimizations that might be possible
    when doing bulk operations

    Ultimately this method will look up the user's preference
    to which NotificationChannel to distribute this over.

    ARGS:
        - user_ids: an iterator that we can enumerate over, say a list or a generator or a ORM resultset
        - msg: A NotificationMessage

    IMPORTANT: If caller wishes to send in a resutset from a Django ORM query, you must
    only select the 'id' column and flatten the results. For example, to send a notification
    to everyone in the Users table, do:

        num_sent = bulk_publish_notification_to_users(
            User.objects.values_list('id', flat=True).all(),
            msg
        )

    """

    if (not isinstance(user_ids, list) and not
            isinstance(user_ids, types.GeneratorType) and not
            isinstance(user_ids, ValuesListQuerySet)):

        err_msg = (
            'bulk_publish_notification_to_users() can only be called with a user_ids argument '
            'of type list, GeneratorType, or ValuesListQuerySet. Type {arg_type} was passed in!'
            .format(arg_type=type(user_ids))
        )
        raise TypeError(err_msg)

    # validate the msg, this will raise a ValidationError if there
    # is something malformatted or missing in the NotificationMessage
    msg.validate()

    # get the system defined msg_type -> channel mapping
    # note, when we enable user preferences, we will
    # have to change this
    channel = get_notification_channel(None, msg.msg_type)

    num_sent = channel.bulk_dispatch_notification(user_ids, msg)

    #
    # Here is where we will tie into the Analytics pipeline
    #

    return num_sent
