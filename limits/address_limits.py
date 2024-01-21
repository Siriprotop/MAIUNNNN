class AddressLimits:
    def __init__(self, dbs):
        self.dbs = dbs
        self.daily_limit = 2
        self.weekly_limit = 5
        self.exceptions = ["6964683351", "6706853874", "6961308641"]

    def can_send_address(self, user_id, date):
        if str(user_id) in self.exceptions:
            return True
        weekly_addresses_count = self.dbs.get_weekly_addresses_count(user_id,)
        daily_addresses_count = self.dbs.get_daily_addresses_count(user_id)

        # Check against the daily and weekly limits
        return daily_addresses_count < self.daily_limit and weekly_addresses_count < self.weekly_limit