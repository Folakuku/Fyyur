# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
csrf.init_app(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []
    location = (
        db.session.query(Venue)
        .with_entities(Venue.city, Venue.state)
        .distinct(Venue.city, Venue.state)
        .all()
    )
    venues = (
        db.session.query(Venue)
        .with_entities(Venue.city, Venue.state, Venue.id, Venue.name)
        .all()
    )
    for i in location:
        data.append({"city": i[0], "state": i[1], "venues": []})
        for j in venues:
            if (j[0] == i[0]) and (j[1] == i[1]):
                num_shows = (
                    db.session.query(Show)
                    .filter(Show.venue_id == j[2])
                    .filter(Show.start_time > datetime.now())
                    .count()
                )
                data[-1]["venues"].append(
                    {"id": j[2], "name": j[3], "num_upcoming_shows": num_shows}
                )
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    keyword = request.form.get("search_term")
    venues = db.session.query(Venue).filter(Venue.name.ilike(f"%{keyword}%")).all()
    response = {"count": len(venues), "data": []}
    for venue in venues:
        num_shows = (
            db.session.query(Show)
            .filter(Show.venue_id == venue.id, Show.start_time > datetime.now())
            .count()
        )
        response["data"].append(
            {"id": venue.id, "name": venue.name, "num_upcoming_shows": num_shows}
        )
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    dat = (
        db.session.query(Venue)
        .with_entities(
            Venue.id,
            Venue.name,
            Venue.genres,
            Venue.address,
            Venue.city,
            Venue.state,
            Venue.phone,
            Venue.website,
            Venue.facebook_link,
            Venue.seeking_talent,
            Venue.seeking_description,
            Venue.image_link,
        )
        .filter_by(id=venue_id)
        .first()
    )
    (
        Id,
        name,
        genres,
        address,
        city,
        state,
        phone,
        website,
        facebook_link,
        seeking_talent,
        seeking_description,
        image_link,
    ) = dat
    venue = {
        "id": Id,
        "name": name,
        "genres": genres,
        "address": address,
        "city": city,
        "state": state,
        "phone": phone,
        "website": website,
        "facebook_link": facebook_link,
        "seeking_talent": seeking_talent,
        "seeking_description": seeking_description,
        "image_link": image_link,
    }
    venue["past_shows"] = []
    past_shows = (
        db.session.query(Show)
        .join(Artist)
        .filter(
            Show.venue_id == venue_id,
            Show.start_time < datetime.now(),
        )
        .with_entities(Artist.id, Artist.name, Artist.image_link, Show.start_time)
    ).all()
    for past_show in past_shows:
        venue["past_shows"].append(
            {
                "artist_id": past_show[0],
                "artist_name": past_show[1],
                "artist_image_link": past_show[2],
                "start_time": str(past_show[3]),
            }
        )
    venue["upcoming_shows"] = []
    upcoming_shows = (
        db.session.query(Show)
        .join(Artist)
        .filter(
            Show.venue_id == venue_id,
            Show.start_time > datetime.now(),
        )
        .with_entities(Artist.id, Artist.name, Artist.image_link, Show.start_time)
    ).all()
    for upcoming_show in upcoming_shows:
        venue["upcoming_shows"].append(
            {
                "artist_id": upcoming_show[0],
                "artist_name": upcoming_show[1],
                "artist_image_link": upcoming_show[2],
                "start_time": str(upcoming_show[3]),
            }
        )
    venue["past_shows_count"] = len(venue["past_shows"])
    venue["upcoming_shows_count"] = len(venue["upcoming_shows"])
    return render_template("pages/show_venue.html", venue=venue)


#  Update
#  ----------------------------------------------------------------
@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = db.session.query(Venue).filter_by(id=venue_id).first()
    form = VenueForm(obj=venue)
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    try:
        venue = db.session.query(Venue).filter_by(id=venue_id).first()
        form = VenueForm(request.form)
        if not form.validate():
            raise ValidationError()
        if form.seeking_talent.data == False:
            form.seeking_description.data = None
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        flash("Venue " + request.form["name"] + " was successfully updated!")
    except:
        db.session.rollback()
        if form.errors:
            flash(form.errors)
        flash(
            "An error occurred. Venue "
            + request.form["name"]
            + " could not be updated."
        )
    finally:
        db.session.close()
        return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    try:
        form = VenueForm(request.form)
        if form.validate():
            if form.seeking_talent.data == False:
                form.seeking_description.data = None
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                website=form.website.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
            )
        db.session.add(venue)
        db.session.commit()
        flash("Venue " + request.form["name"] + " was successfully listed!")
    except Exception as e:
        print(e)
        print(f"form error:{form.errors}")
        print(sys.exc_info())
        db.session.rollback()
        if form.errors:
            flash(form.errors)
        flash(
            "An error occurred. Venue " + request.form["name"] + " could not be listed."
        )
    finally:
        db.session.close()
        return render_template("pages/home.html")


@app.route("/venues/<int:venue_id>/delete", methods=["POST"])
def delete_venue(venue_id):
    try:
        venue = db.session.query(Venue).filter_by(id=venue_id).first()
        shows = db.session.query(Show).filter_by(venue_id=venue_id).all()
        if len(shows) >= 1:
            for show in shows:
                db.session.delete(show)

        db.session.delete(venue)
        db.session.commit()
        flash("Venue successfully deleted.")
    except:
        flash(
            "An error occurred. Venue "
            + request.form["name"]
            + " could not be deleted."
        )
        db.session.rollback()
    finally:
        db.session.close()
        return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    data = db.session.query(Artist).with_entities(Artist.id, Artist.name).all()
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    keyword = request.form.get("search_term")
    artists = (
        db.session.query(Artist)
        .with_entities(Artist.id, Artist.name)
        .filter(Artist.name.ilike(f"%{keyword}%"))
        .all()
    )
    response = {"count": len(artists), "data": []}
    for artist in artists:
        num_shows = (
            db.session.query(Show)
            .filter(Show.artist_id == artist.id, Show.start_time > datetime.now())
            .count()
        )
        response["data"].append(
            {"id": artist.id, "name": artist.name, "num_upcoming_shows": num_shows}
        )
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = db.session.query(Artist).filter_by(id=artist_id).first()
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }
    data["past_shows"] = []
    past_shows = (
        db.session.query(Show)
        .join(Venue)
        .filter(
            Show.artist_id == artist_id,
            Show.start_time < datetime.now(),
        )
        .with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time)
    ).all()
    for past_show in past_shows:
        data["past_shows"].append(
            {
                "venue_id": past_show.id,
                "venue_name": past_show.name,
                "venue_image_link": past_show.image_link,
                "start_time": str(past_show.start_time),
            }
        )
    data["upcoming_shows"] = []
    upcoming_shows = (
        db.session.query(Show)
        .join(Venue)
        .filter(
            Show.artist_id == artist_id,
            Show.start_time > datetime.now(),
        )
        .with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time)
    ).all()
    for upcoming_show in upcoming_shows:
        data["upcoming_shows"].append(
            {
                "venue_id": upcoming_show.id,
                "venue_name": upcoming_show.name,
                "venue_image_link": upcoming_show.image_link,
                "start_time": str(upcoming_show.start_time),
            }
        )
    data["past_shows_count"] = len(data["past_shows"])
    data["upcoming_shows_count"] = len(data["upcoming_shows"])

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = db.session.query(Artist).filter_by(id=artist_id).first()
    form = ArtistForm(obj=artist)
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    try:
        form = ArtistForm(request.form)
        if not form.validate():
            raise ValidationError()
        if form.seeking_venue.data == False:
            form.seeking_description.data = None
        artist = db.session.query(Artist).filter_by(id=artist_id).first()
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.image_link = form.image_link.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.website = form.website.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully updated!")
    except:
        db.session.rollback()
        if form.errors:
            flash(form.errors)
        flash(
            "An error occurred. Artist "
            + request.form["name"]
            + " could not be updated."
        )
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    try:
        form = ArtistForm(request.form)
        if form.validate():
            if form.seeking_venue.data == False:
                form.seeking_description.data = None

            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                website=form.website.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
            )
        db.session.add(artist)
        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully listed!")
    except:
        db.session.rollback()
        if form.errors:
            flash(form.errors)
        flash(
            "An error occurred. Artist "
            + request.form["name"]
            + " could not be listed."
        )
    finally:
        db.session.close()
        return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    shows = (
        db.session.query(Show)
        .join(Venue)
        .join(Artist)
        .with_entities(
            Venue.id,
            Venue.name,
            Artist.id,
            Artist.name,
            Artist.image_link,
            Show.start_time,
        )
    ).all()
    data = []
    for show in shows:
        data.append(
            {
                "venue_id": show[0],
                "venue_name": show[1],
                "artist_id": show[2],
                "artist_name": show[3],
                "artist_image_link": show[4],
                "start_time": str(show[5]),
            }
        )
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    try:
        # renders form. do not touch.
        form = ShowForm()
    except:
        db.session.rollback()
    finally:
        return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    try:
        form = ShowForm(request.form)

        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data,
        )
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        flash("An error occurred. Show could not be listed. Check id provided.")
    finally:
        db.session.close()
        return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
