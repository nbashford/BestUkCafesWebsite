"""
Helper class to hold Current user refine search options when filtering
for Cafes to be displayed - since Flask form data is reset after submissions
"""
from db_models import db, Cafes


def get_cafes_city(name):
    """query cafes db to get the city address from a given cafe name"""
    cafe = db.session.execute(db.select(Cafes).where(
        Cafes.name == name)).scalar()
    city = cafe.city
    return city


class SearchFilterValues:
    """Helper class to hold Current user refine search options from page 'All Cafes'.
    Since the refine search form - after submitting - will not hold the previously selected data, the data
     is stored in this class - and is used to update the refine search select fields - for better UX."""
    # holds the refine search form options (User selected data - not placeholder)
    name = None
    city = None
    wifi = None
    pets = None
    laptop = None
    open_day = None

    # for default values displayed in the refine search form (Placeholder - no user selected option)
    name_label = "Any"
    city_label = "Any"
    wifi_label = "All"
    pets_label = "All"
    laptop_label = "All"
    open_day_label = "Select"

    def update_name(self, name=None):
        """updates the name"""
        self.__class__.name = name if name else None
        self.__class__.name_label = name if name else "Any"
        if name:  # if name passed then update the city location
            self.update_city(get_cafes_city(name))

    def update_city(self, location=None):
        """updates the city"""
        self.__class__.city = location if location else None
        self.__class__.city_label = location if location else "Any"

    def update_wifi(self, reset=False):
        """updates the wi-fi variables"""
        if reset:
            self.__class__.wifi = None
            self.__class__.wifi_label = "All"
        else:
            self.__class__.wifi = "Free Wi-Fi"  # for the db query
            self.__class__.wifi_label = "Yes"  # update displayed select form

    def update_pets(self, reset=False):
        """updates the pets variables"""
        if reset:
            self.__class__.pets = None
            self.__class__.pets_label = "All"
        else:
            self.__class__.pets = "Pet Friendly"
            self.__class__.pets_label = "Yes"

    def update_laptop(self, reset=False):
        """updates the laptop variables"""
        if reset:
            self.__class__.laptop = None
            self.__class__.laptop_label = "All"
        else:
            self.__class__.laptop = "Laptop Friendly"
            self.__class__.laptop_label = "Yes"

    def update_open_day(self, day=False):
        """updates the closed day variables"""
        if not day:
            self.__class__.open_day = None
            self.__class__.open_day_label = "Select"
        else:
            self.__class__.open_day = day
            self.__class__.open_day_label = day

    def reset_all(self):
        self.update_name()
        self.update_city()
        self.update_wifi(reset=True)
        self.update_pets(reset=True)
        self.update_laptop(reset=True)
        self.update_open_day()
