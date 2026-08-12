from .db_sessions import DbSessionMiddleware
from .user import UserMiddleware
from .subscription import CheckSubscriptionMiddleware
from .activity import ActivityMiddleware
from loader import dp, db


dp.update.middleware.register(DbSessionMiddleware(db))
dp.update.middleware.register(UserMiddleware(db))
dp.update.middleware.register(ActivityMiddleware())
dp.message.middleware.register(CheckSubscriptionMiddleware(db))
dp.callback_query.middleware.register(CheckSubscriptionMiddleware(db))
