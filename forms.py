from datetime import datetime
from flask_wtf import Form, CSRFProtect
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    DateTimeField,
    BooleanField,
)
from wtforms.validators import DataRequired, AnyOf, URL, ValidationError, Regexp
from enums import Genre, State
import re

csrf = CSRFProtect()


def is_valid_phone(number):
    regex = re.compile("^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$")
    return regex.match(number)


state_choices = [
    ("AL", "AL"),
    ("AK", "AK"),
    ("AZ", "AZ"),
    ("AR", "AR"),
    ("CA", "CA"),
    ("CO", "CO"),
    ("CT", "CT"),
    ("DE", "DE"),
    ("DC", "DC"),
    ("FL", "FL"),
    ("GA", "GA"),
    ("HI", "HI"),
    ("ID", "ID"),
    ("IL", "IL"),
    ("IN", "IN"),
    ("IA", "IA"),
    ("KS", "KS"),
    ("KY", "KY"),
    ("LA", "LA"),
    ("ME", "ME"),
    ("MT", "MT"),
    ("NE", "NE"),
    ("NV", "NV"),
    ("NH", "NH"),
    ("NJ", "NJ"),
    ("NM", "NM"),
    ("NY", "NY"),
    ("NC", "NC"),
    ("ND", "ND"),
    ("OH", "OH"),
    ("OK", "OK"),
    ("OR", "OR"),
    ("MD", "MD"),
    ("MA", "MA"),
    ("MI", "MI"),
    ("MN", "MN"),
    ("MS", "MS"),
    ("MO", "MO"),
    ("PA", "PA"),
    ("RI", "RI"),
    ("SC", "SC"),
    ("SD", "SD"),
    ("TN", "TN"),
    ("TX", "TX"),
    ("UT", "UT"),
    ("VT", "VT"),
    ("VA", "VA"),
    ("WA", "WA"),
    ("WV", "WV"),
    ("WI", "WI"),
    ("WY", "WY"),
]

genres_choices = [
    ("Alternative", "Alternative"),
    ("Blues", "Blues"),
    ("Classical", "Classical"),
    ("Country", "Country"),
    ("Electronic", "Electronic"),
    ("Folk", "Folk"),
    ("Funk", "Funk"),
    ("Hip-Hop", "Hip-Hop"),
    ("Heavy Metal", "Heavy Metal"),
    ("Instrumental", "Instrumental"),
    ("Jazz", "Jazz"),
    ("Musical Theatre", "Musical Theatre"),
    ("Pop", "Pop"),
    ("Punk", "Punk"),
    ("R&B", "R&B"),
    ("Reggae", "Reggae"),
    ("Rock n Roll", "Rock n Roll"),
    ("Soul", "Soul"),
    ("Other", "Other"),
]


class ShowForm(Form):
    artist_id = StringField("artist_id", validators=[DataRequired()])
    venue_id = StringField("venue_id", validators=[DataRequired()])
    start_time = DateTimeField(
        "start_time", validators=[DataRequired()], default=datetime.today()
    )


class VenueForm(Form):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField("state", validators=[DataRequired()], choices=State.choices())
    address = StringField("address", validators=[DataRequired()])
    phone = StringField(
        "phone",
        validators=[
            DataRequired(),
            Regexp(
                regex="^[0-9]{3}-?[0-9]{3}-?[0-9]{4}$",
                flags=0,
                message="Invalid phone number",
            ),
        ],
    )
    image_link = StringField("image_link", validators=[DataRequired(), URL()])
    genres = SelectMultipleField(
        # TODO implement enum restriction
        "genres",
        validators=[DataRequired()],
        choices=Genre.choices(),
    )
    facebook_link = StringField("facebook_link", validators=[DataRequired(), URL()])
    website = StringField("website_link", validators=[DataRequired(), URL()])
    seeking_talent = BooleanField("seeking_talent")
    seeking_description = StringField("seeking_description")

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        if not is_valid_phone(self.phone.data):
            self.phone.errors.append("Invalid phone.")
            return False
        if not set(self.genres.data).issubset(dict(Genre.choices()).keys()):
            self.genres.errors.append("Invalid genres.")
            return False
        if self.state.data not in dict(State.choices()).keys():
            self.state.errors.append("Invalid state.")
            return False
        # if pass validation
        return True


class ArtistForm(Form):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField("state", validators=[DataRequired()], choices=State.choices())
    phone = StringField(
        # TODO implement validation logic for phone
        "phone",
        validators=[
            DataRequired(),
            Regexp(
                regex="^[0-9]{3}-?[0-9]{3}-?[0-9]{4}$",
                flags=0,
                message="Invalid phone number",
            ),
        ],
    )
    image_link = StringField("image_link", validators=[DataRequired(), URL()])
    genres = SelectMultipleField(
        "genres", validators=[DataRequired()], choices=Genre.choices()
    )
    facebook_link = StringField(
        "facebook_link",
        validators=[DataRequired(), URL()],
    )

    website = StringField("website_link", validators=[DataRequired(), URL()])
    seeking_venue = BooleanField("seeking_venue")
    seeking_description = StringField("seeking_description")

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        if not is_valid_phone(self.phone.data):
            self.phone.errors.append("Invalid phone.")
            return False
        if not set(self.genres.data).issubset(dict(Genre.choices()).keys()):
            self.genres.errors.append("Invalid genres.")
            return False
        if self.state.data not in dict(State.choices()).keys():
            self.state.errors.append("Invalid state.")
            return False
        # if pass validation
        return True
