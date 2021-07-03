#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler, error
from flask_wtf import Form
from forms import *
from datetime import datetime
from flask_migrate import Migrate
from models import *
from sqlalchemy.exc import SQLAlchemyError

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Moved to models.py

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    """Populates venue details"""
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    data = []
    venues = Venue.query.all()
    places = Venue.query.distinct(Venue.city, Venue.state).all()

    for place in places:
        data.append({
            'city': place.city,
            'state': place.state,
            'venues': [{
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
            } for venue in venues if
                venue.city == place.city and venue.state == place.state]
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """Search for a Venue"""
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    search_result = Venue.query.filter(
        Venue.name.ilike(f'%{search_term}%')).all()
    data = []

    for el in search_result:
        data.append({
            "id": el.id,
            "name": el.name,
            "num_upcoming_shows": len(Show.query.filter(Show.venue_id == el.id).filter(Show.start_time > datetime.now()).all()),
        })

    response = {
        "count": len(search_result),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """Shows the venue page with the given venue_id"""
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    venue = Venue.query.get(venue_id)

    if not venue:
        return render_template('errors/404.html')

    past_shows_data = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
    past_shows = []

    for el in past_shows_data:
        past_shows.append({
            "artist_id": el.artist_id,
            "artist_name": el.artist.name,
            "artist_image_link": el.artist.image_link,
            "start_time": el.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    upcoming_shows_data = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()
    upcoming_shows = []

    for el in upcoming_shows_data:
        upcoming_shows.append({
            "artist_id": el.artist_id,
            "artist_name": el.artist.name,
            "artist_image_link": el.artist.image_link,
            "start_time": el.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            address = request.form['address']
            phone = request.form['phone']
            genres = request.form.getlist('genres')
            image_link = request.form['image_link']
            facebook_link = request.form['facebook_link']
            website = request.form['website_link']
            seeking_talent = True if 'seeking_talent' in request.form else False
            seeking_description = request.form['seeking_description']
            venue = Venue(name=name,
                          city=city,
                          state=state,
                          address=address,
                          phone=phone,
                          genres=genres,
                          facebook_link=facebook_link,
                          image_link=image_link,
                          website=website,
                          seeking_talent=seeking_talent,
                          seeking_description=seeking_description)
            db.session.add(venue)
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            message.append(field + ': (' + '|'.join(errors) + ')')
        print(message)
        flash('The Venue data is not valid. Please try again!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occurred while deleting {}. Action could not be completed', format(
            venue_id))
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database

    data = Artist.query.all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term', '')
    search_result = Artist.query.filter(
        Artist.name.ilike(f'%{search_term}%')).all()
    data = []

    for result in search_result:
        data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(Show.query.filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all()),
        })

    response = {
        "count": len(search_result),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)

    if not artist:
        return render_template('errors/404.html')

    past_shows_data = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
    past_shows = []

    for el in past_shows_data:
        past_shows.append({
            "venue_id": el.venue_id,
            "venue_name": el.venue.name,
            "venue_image_link": el.venue.image_link,
            "start_time": el.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    upcoming_shows_data = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
    upcoming_shows = []

    for el in upcoming_shows_data:
        upcoming_shows.append({
            "venue_id": el.venue_id,
            "venue_name": el.venue.name,
            "venue_image_link": el.venue.image_link,
            "start_time": el.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # TODO: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)

    if artist:
        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.genres.data = artist.genres
        form.facebook_link.data = artist.facebook_link
        form.image_link.data = artist.image_link
        form.website_link.data = artist.website
        form.seeking_venue.data = artist.seeking_venue
        form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    # artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form, meta={'csrf': False})
    artist = Artist.query.get_or_404(artist_id)
     
    if form.validate():
        try:
            artist.name = request.form['name']
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            artist.genres = request.form.getlist('genres')
            artist.image_link = request.form['image_link']
            artist.facebook_link = request.form['facebook_link']
            artist.website = request.form['website_link']
            artist.seeking_venue = True if 'seeking_venue' in request.form else False
            artist.seeking_description = request.form['seeking_description']

            # artist.name = form.name.data
            # artist.city = form.city.data
            # artist.state = form.state.data
            # artist.phone = form.phone.data
            # artist.genres = form.genres.data
            # artist.image_link = form.image_link.data
            # artist.facebook_link = form.facebook_link.data
            # artist.website = form.website_link.data
            # artist.seeking_venue = True if 'seeking_venue' in request.form else False
            # artist.seeking_description = form.seeking_description.data

            db.session.commit()
            flash('Details for the Artist {} are updated'.format(artist_id))
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            flash('Update failed for Artist {}'.format(artist_id))
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            message.append(field + ': (' + '|'.join(errors) + ')')
        print(message)
        flash('The Artist data is not valid. Please try again!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)

    if venue:
        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.address.data = venue.address
        form.genres.data = venue.genres
        form.facebook_link.data = venue.facebook_link
        form.image_link.data = venue.image_link
        form.website_link.data = venue.website
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.filter_by(id = venue_id).first()
    print('Venue ID - {} {}'.format(venue.id, venue.seeking_description))
    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            venue.name = request.form['name']
            venue.city = request.form['city']
            venue.state = request.form['state']
            venue.address = request.form['address']
            venue.phone = request.form['phone']
            venue.genres = request.form.getlist('genres')
            venue.image_link = request.form['image_link']
            venue.facebook_link = request.form['facebook_link']
            venue.website = request.form['website_link']
            venue.seeking_talent = True if 'seeking_talent' in request.form else False
            venue.seeking_description = request.form['seeking_description']
            print('Seeking description - {}'.format(venue.seeking_description))
            db.session.commit()
            flash('Details for the Venue {} are updated'.format(venue_id))
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            flash('Update failed for Venue {}'.format(venue_id))
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            message.append(field + ': (' + '|'.join(errors) + ')')
        print(message)
        flash('The Venue data is not valid. Please try again!')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            phone = request.form['phone']
            genres = request.form.getlist('genres')
            facebook_link = request.form['facebook_link']
            image_link = request.form['image_link']
            website = request.form['website_link']
            seeking_venue = True if 'seeking_venue' in request.form else False
            seeking_description = request.form['seeking_description']

            artist = Artist(name=name,
                            city=city,
                            state=state,
                            phone=phone,
                            genres=genres,
                            facebook_link=facebook_link,
                            image_link=image_link,
                            website=website,
                            seeking_venue=seeking_venue,
                            seeking_description=seeking_description)

            db.session.add(artist)
            db.session.commit()
            # on successful db insert, flash success
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            message.append(field + ': (' + '|'.join(errors) + ')')
        print(message)
        flash('The Artist data is not valid. Please try again!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows = db.session.query(Show).join(Artist).join(Venue).all()
    data = []

    for el in shows:
        data.append({
            "venue_id": el.venue_id,
            "venue_name": el.venue.name,
            "artist_id": el.artist_id,
            "artist_name": el.artist.name,
            "artist_image_link": el.artist.image_link,
            "start_time": el.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    form = ShowForm(request.form, meta={'csrf': False})

    if form.validate():
        try:
            show = Show(
                venue_id=request.form['venue_id'],
                artist_id=request.form['artist_id'],
                start_time=request.form['start_time'],
            )

            db.session.add(show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Show could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            message.append(field + ': (' + '|'.join(errors) + ')')
            flash('The Show data is not valid. Please try again!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
