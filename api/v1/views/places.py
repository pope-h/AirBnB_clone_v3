#!/usr/bin/python3
"""Creates a view for City objects"""

import json
from models import storage
from models.city import City
from models.place import Place
from models.user import User
from models.state import State
from models.amenity import Amenity
from api.v1.views import app_views
from flask import abort, request, jsonify


@app_views.route('/cities/<city_id>/places', methods=['GET'],
                 strict_slashes=False)
def getPlaces(city_id):
    """gets all the places associated with the city_id"""
    city = storage.get(City, city_id)
    if not city:
        abort(404)
    places = [place.to_dict() for place in storage.all(Place).values()
              if place.city_id == city_id]
    return jsonify(places), 200


@app_views.route('/places/<place_id>', methods=['GET'], strict_slashes=False)
def getPlace(place_id):
    """gets a single place based on it's id"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    return jsonify(place.to_dict()), 200


@app_views.route('/places/<place_id>', methods=['DELETE'],
                 strict_slashes=False)
def deletePlace(place_id):
    """deletes a place from db"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    else:
        storage.delete(place)
        storage.save()
        return jsonify({}), 200


@app_views.route('/cities/<city_id>/places', methods=['POST'],
                 strict_slashes=False)
def addPlace(city_id):
    """adds a new place to the db with city_id"""
    city = storage.get(City, city_id)
    if not city:
        abort(404)

    if not request.is_json:
        abort(400, "Not a JSON")

    obj = request.get_json()

    if 'user_id' not in obj:
        abort(400, "Missing user_id")

    user_id = obj['user_id']
    user = storage.get(User, user_id)
    if not user:
        abort(404)

    if 'name' not in obj:
        abort(400, "Missing name")

    obj['city_id'] = city_id
    place = Place(**obj)
    storage.new(place)
    storage.save()
    return jsonify(place.to_dict()), 201


@app_views.route('/places/<place_id>', methods=['PUT'], strict_slashes=False)
def updatePlace(place_id):
    """updates a place"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)

    if not request.is_json:
        abort(400, "Not a JSON")

    data = request.get_json()
    for key, value in data.items():
        if key not in ['id', 'user_id', 'city_id', 'created_at', 'updated_at']:
            setattr(place, key, value)
    storage.save()
    return jsonify(place.to_dict()), 200


@app_views.route('/places_search', methods=['POST'], strict_slashes=False)
def places_search():
    """
    Retrieve place objects based on the JSON in the body
    of the request
    """

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    if data and len(data):
        states = data.get('states', None)
        cities = data.get('cities', None)
        amenities = data.get('amenities', None)

    if not data or not len(data) or (
            not states and
            not cities and
            not amenities):
        places = storage.all(Place).values()
        list_places = []
        for place in places:
            list_places.append(place.to_dict())

        return jsonify(list_places)

    list_places = []
    if states:
        states_obj = [storage.get(State, s_id) for s_id in states]
        for state in states_obj:
            if state:
                for city in state.cities:
                    if city:
                        for place in city.places:
                            list_places.append(place)

    if cities:
        city_obj = [storage.get(City, c_id) for c_id in cities]
        for city in city_obj:
            if city:
                for place in city.places:
                    if place not in list_places:
                        list_places.append(place)

    if amenities:
        if not list_places:
            list_places = storage.get(Place).values()
        amenities_obj = [storage.get(Amenity, a_id) for a_id in amenities]
        list_places = [place for place in list_places if all([
                       amen in place.amenities for amen in amenities_obj])]

    places = []
    for place in list_places:
        res = place.to_dict()
        res.pop('amenities', None)
        places.append(res)

    return jsonify(places)
