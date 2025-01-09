"""
File for defining the SQLAlchemy database tables and for populating the
Cafes db with data from the all_cafes_csv.csv file
"""
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text
from flask_login import UserMixin
import csv

# set up db and initialise with flask app
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Many-to-Many relationship table between Cafes and Users
favourites_table = db.Table(
    "favourites",
    db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),  # link to User
    db.Column("cafe_id", db.Integer, db.ForeignKey("cafes.id"), primary_key=True),  # link to Cafe
    db.Column("added_at", db.DateTime, default=datetime.datetime.now))


class Cafes(db.Model):
    """database table - adding cafe data to database"""
    __tablename__ = 'cafes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    link: Mapped[str] = mapped_column(String(150), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    street: Mapped[str] = mapped_column(String(100), nullable=False)
    opening: Mapped[str] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str] = mapped_column(String(10), nullable=False)
    closed: Mapped[str] = mapped_column(String(100), nullable=True)
    url_location: Mapped[str] = mapped_column(String(250), nullable=True)
    wifi: Mapped[str] = mapped_column(String(50), nullable=True)
    laptop: Mapped[str] = mapped_column(String(50), nullable=True)
    pets: Mapped[str] = mapped_column(String(50), nullable=True)
    latitude: Mapped[str] = mapped_column(String(50), nullable=True)
    longitude: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    # One-to-Many association to comments
    cafe_comments = relationship("Comment", back_populates="cafe_entry")

    # Relationship linking to users through favourites_table
    saved_by = relationship(
        "Users",
        secondary=favourites_table,
        back_populates="favourites")


class Users(UserMixin, db.Model):
    """Stores user login information for sign up and login functionality"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=True)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    pswd: Mapped[str] = mapped_column(String(100), nullable=False)  # hashed password

    # Relationship linking to cafes through favourites_table
    favourites = relationship(
        "Cafes",
        secondary=favourites_table,
        back_populates="saved_by")

    # One-to-Many relationship to Comments
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    """Stores comments for Cafes"""
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Comments -> User (Many to One)
    author_id: Mapped[int] = mapped_column(Integer,
                                           db.ForeignKey("users.id"), nullable=False)
    comment_author = relationship("Users", back_populates="comments")

    # Comments -> Cafes (Many to One)
    cafe_id: Mapped[int] = mapped_column(Integer,
                                         db.ForeignKey("cafes.id"), nullable=False)
    cafe_entry = relationship("Cafes", back_populates="cafe_comments")


class NewCafes(db.Model):
    """database table - adding NEW cafe data to database. Separate to 'Cafes' db - so can vet before adding."""
    __tablename__ = 'new_cafes'  # for foreign key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    link: Mapped[str] = mapped_column(String(150), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    street: Mapped[str] = mapped_column(String(100), nullable=False)
    opening: Mapped[str] = mapped_column(String(100), nullable=True)
    closed: Mapped[str] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str] = mapped_column(String(10), nullable=False)
    url_location: Mapped[str] = mapped_column(String(250), nullable=True)
    wifi: Mapped[str] = mapped_column(String(50), nullable=True)
    laptop: Mapped[str] = mapped_column(String(50), nullable=True)
    pets: Mapped[str] = mapped_column(String(50), nullable=True)
    latitude: Mapped[str] = mapped_column(String(50), nullable=True)
    longitude: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.datetime.now)



def get_days_closed_string(original_string):
    """
    Formats the 'opening string' to state 'closed' on closed days.
    :returns string of days closed, separated by '|'
    """
    closed_string = "None"
    days_closed = []
    if 'Closed' in original_string:  # if one + days are closed
        days = original_string.split('|')
        for day in days:  # for each day of week
            if 'Closed' in day:
                weekday = day.split(':')[0] # get the day
                if not ' - ' in day:
                    days_closed.append(weekday)
                else:  # i.e. multiple days string: 'Saturday - Sunday'
                    days_closed.append(weekday.split("-")[0].strip())
                    days_closed.append(weekday.split("-")[1].strip())

    if days_closed:
        # join days closed to single string
        closed_string = "|".join(days_closed)

    return closed_string


def add_data_to_database():
    """
    Adds cafe csv data to Cafes database table.
    Requires the CSV file data generated from the project CafeDataScraping,
    from: https://github.com/nbashford/CafeDataScraping
    """
    # open the cafe csv file
    with open("all_cafes_csv.csv", "r") as file:
        reader = csv.reader(file, delimiter=",")
        rows = list(reader)

        # get the header index numbers for the CSV data
        header = rows[0]
        id_idx = header.index("ID")
        name_idx = header.index("Name")
        link_idx = header.index("Link")
        city_idx = header.index("City")
        street_idx = header.index("Street")
        opening_idx = header.index("Opening")
        postcode_idx = header.index("Postcode")
        url_location_idx = header.index("Url Location")
        wifi_idx = header.index("Wifi")
        laptop_idx = header.index("Laptop Friendly")
        pet_idx = header.index("Pet Friendly")
        lat_idx = header.index("Latitude")
        lon_idx = header.index("Longitude")

        # add each row of CSV cafe data to the Cafes database table
        for row in rows[1:]:
            cafe = Cafes(
                id=int(row[id_idx]),
                name=row[name_idx],
                link=row[link_idx],
                city=row[city_idx],
                street=row[street_idx],
                opening=row[opening_idx],
                closed=get_days_closed_string(row[opening_idx]),  # get closed day (not in CSV)
                postcode=row[postcode_idx],
                url_location=row[url_location_idx],
                wifi=row[wifi_idx],
                laptop=row[laptop_idx],
                pets=row[pet_idx],
                latitude=str(row[lat_idx]),
                longitude=str(row[lon_idx])
            )
            # add and update the Cafes database
            db.session.add(cafe)
            db.session.commit()
