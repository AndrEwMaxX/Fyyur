# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for
)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from models import app, db, Venue, Artist, Show

from datetime import datetime

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app.config.from_object('config')
moment = Moment(app)
db.init_app(app)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:0000@127.0.0.1:5432/fyyur'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium') :
    date = dateutil.parser.parse(value)
    if format == 'full' :
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium' :
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index() :
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues() :
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    """
  data=[{
    "city": "San Francisco",
    "state": "CA",
    "venues": [{
      "id": 1,
      "name": "The Musical Hop",
      "num_upcoming_shows": 0,
    }, {
      "id": 3,
      "name": "Park Square Live Music & Coffee",
      "num_upcoming_shows": 1,
    }]
  }, {
    "city": "New York",
    "state": "NY",
    "venues": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }]
  """
    venue_group = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state)
    data = []
    venues = []
    venue = db.session.query(Venue.id, Venue.name)

    for i in venue :
        venues.append({"id" : i.id, "name" : i.name})

    for j in venue_group:
        data.append({"city" : j.city, "state" : j.state, "venues": venues})    

    return render_template('pages/venues.html', areas=data, venues=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    ven = db.session.query(Venue.name, Venue.id)
    results = {}
    count = 0
    search_term=request.form.get('search_term', '')
    for i in ven:
        if search_term.lower()==(i.name.lower()):
            count += 1
            #results.append({"count": count, "data": [{"id": i.id, "name": i.name}]})
            results={"count": count, "data": [{"id": i.id, "name":i.name,}]}

        else:
            results={"count": 0}

    return render_template('pages/search_venues.html', results=results, search_term=request.form.get('search_term', ''))

    
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
        filter(
            Show.venue_id == Venue.id,
            Show.artist_id == Artist.id,
            Show.start_time < datetime.now()
        ).\
        all()

    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time > datetime.now()
    ).\
    all()

    venue = Venue.query.get(venue_id)
    artist = Artist.query.all()
    show = Show.query.all()

    data={
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
    'past_shows': [{
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, show in past_shows],
    'upcoming_shows': [{
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }


    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form() :
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission() :
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()
    try :
        venue_info = Venue(
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
            seeking_description=form.seeking_description.data
        )
        db.session.add(venue_info)
        db.session.commit()
        flash('Venue ' + form.name.data + ' was successfully listed!')
    except Exception as error :
        db.session.rollback()
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed. ' + str(error))
    finally :
        db.session.close()
    return render_template('pages/home.html')

    # on successful db insert, flash success
    # flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id) :
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists() :
    # TODO: replace with real data returned from querying the database
    artist = Artist.query.order_by('name').all()

    return render_template('pages/artists.html', artists=artist)


@app.route('/artists/search', methods=['POST'])
def search_artists() :
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    art = db.session.query(Artist.name, Artist.id)
    results = {}
    count = 0
    search_term=request.form.get('search_term', '')
    for i in art:
        if search_term.lower()==(i.name.lower()):
            count += 1
            #results.append({"count": count, "data": [{"id": i.id, "name": i.name}]})
            results={"count": count, "data": [{"id": i.id, "name":i.name,}]}
            
    return render_template('pages/search_venues.html', results=results, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id) :

    past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
        Show.venue_id == Venue.id,
        Show.artist_id == Artist.id,
        Show.start_time < datetime.now()
    ).\
    all()

    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
        Show.venue_id == Venue.id,
        Show.artist_id == artist_id,
        Show.start_time > datetime.now()
    ).\
    all()

    artist = Artist.query.get(artist_id)
    venue = Venue.query.all()
    show = Show.query.all()

    data={

        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_talent": artist.seeking_talent,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        'past_shows': [{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for venue, show in past_shows],
        'upcoming_shows': [{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for venue, show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id) :
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
        
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id) :
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()    
    try :
        artist_info = Artist.query.get(artist_id)
        artist = db.session.query(Artist)\
            .filter(Artist.id==artist_id)\
                .update({Artist.name: form.name.data, Artist.city: form.city.data, Artist.state: form.state.data, Artist.phone: form.phone.data, Artist.genres: form.genres.data, Artist.facebook_link: form.facebook_link.data, Artist.website: form.website.data , Artist.seeking_talent: form.seeking_talent.data, Artist.seeking_description: form.seeking_description.data, })

        db.session.commit()
        flash('Artist ' + form.name.data + ' was successfully updated!')
    except Exception as error :
        db.session.rollback()
        flash('An error occurred. Artist ' + form.name.data + ' could not be updated. ' + str(error))
    finally :
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id) :
    form = VenueForm()
    venue = Venue.query.get(venue_id)
  
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id) :
    form = VenueForm()    
    try :
        venue_info = Venue.query.get(venue_id)
        venue = db.session.query(Venue)\
            .filter(Venue.id==venue_id)\
                .update({Venue.name: form.name.data, Venue.city: form.city.data, Venue.state: form.state.data, Venue.phone: form.phone.data, Venue.genres: form.genres.data, Venue.facebook_link: form.facebook_link.data, Venue.website: form.website.data, Venue.seeking_talent: form.seeking_talent.data, Venue.seeking_description: form.seeking_description.data, })

        db.session.commit()
        flash('Venue ' + form.name.data + ' was successfully updated!')
    except Exception as error :
        db.session.rollback()
        flash('An error occurred. Venue ' + form.name.data + ' could not be updated. ' + str(error))
    finally :
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form() :
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission() :

    form = VenueForm()
    try :
        artist_info = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            website=form.website.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(artist_info)
        db.session.commit()
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except Exception as error :
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed. ' + str(error))
    finally :
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows() :
    res = []
    show = db.session.query(Venue.id, Venue.name, Artist.id, Artist.name, Show.start_time) \
        .join(Venue, Show.venue_id == Venue.id) \
        .join(Artist, Show.artist_id == Artist.id)

    for i in show :
        res.append(
            {'venue_id' : i[0], 'venue_name' : i[1], 'artist_id' : i[2], 'artist_name' : i[3], 'start_time' : i[4]})

    return render_template('pages/shows.html', shows=res)


@app.route('/shows/create')
def create_shows() :
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission() :
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm()
    try :
        show_info = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )
        db.session.add(show_info)
        db.session.commit()

        flash('Show was successfully listed!')
    except Exception as error :
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist could not be listed. ' + str(error))
    finally :
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error) :
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error) :
    return render_template('errors/500.html'), 500


if not app.debug :
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__' :
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
