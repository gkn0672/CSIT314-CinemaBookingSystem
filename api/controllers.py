from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.db import DatabaseError
from django.http import JsonResponse
from core.models import User
from core.models import Profile
from .serializers import UserSerializer, UpdateMovieSerializer
from .serializers import ProfileSerializer
from .serializers import RegisterAccount
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.utils import timezone
from datetime import datetime, timedelta
from uuid import UUID
# Create your views here.
# LOGIN 
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework import status
# LOGOUT
from django.contrib.auth import logout
from rest_framework.response import Response
# UPDATE
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from core.models import CustomUserManager
# MOVIE
from rest_framework.decorators import api_view, permission_classes
from core.models import Movie, CinemaRoom, FoodandBeverage, MovieSession, FnBBooking
from .serializers import MovieSerializer, CinemaRoomSerializer, FoodandBeverageSerializer, MovieSessionSerializer
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseServerError
from django.core.exceptions import ValidationError
# PURCHASE BOOKING
from .serializers import PurchaseTicketSerializer
from core.models import MovieBooking
# Report
from core.models import Report

# Login/logout
class AccountController:
    #GETS USER ACCOUNT
    @api_view(['GET'])
    def getUserAccount(request):
        result = User.userall()

        user = [u for u in result]
        data = [{'user_id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in user]
        return Response(data)
        

    #REGISTERS ACCOUNT PARAMETER: PW
    @api_view(['POST'])
    def RegisterAccount(request):
        try:
            # Encrypt the password before passing it to the serializer instance
            username = request.data.get('username')
            password = request.data.get('password')
            email = request.data.get('email')
            role = request.data.get('role')
            if not password:
                return Response({"error": "Password cannot be empty"}, status=400)
            if not role:
                role = 'Customer'
            user = User()
            user.usercreate(username, password, email, role)
            return Response(status=status.HTTP_200_OK)
        except DatabaseError as e:
            return Response({"error": "Bad data"}, status=500)
        
class LoginView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    #LOGIN(username, pw) 
    @api_view(['POST'])
    def login(request):
        username = request.data.get('username')
        password = request.data.get('password')
        myuser = User()
        token = myuser.userauthenticate(request, username, password)
        if token is not None:
            response_data = {
                    'message': 'Login success',
                    'token': token.key
            }
            response = Response(response_data, status=status.HTTP_200_OK)
            response.set_cookie('token', token.key)  # add session cookie
            return response
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    #LOGOUT()
    @api_view(['POST'])
    def logout(request):
        if not request.user.is_authenticated:
            raise PermissionDenied()
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        response = Response({'message': 'Logout success'}, status=status.HTTP_200_OK)
        response.delete_cookie('token')  # remove session cookie
        myuser = User()
        myuser.userlogout(request)
        return response


# User account
class GetUserView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['GET'])
    def getUser(request):
        user = request.user
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
        return Response(user_data, status=status.HTTP_200_OK)
    
class UpdateUser(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def updateUser(request):
        try:
            user1 = request.user
            if user1.role != 'UserAdmin':
                return Response({'message': 'You don\'t have permission to update account'}, status=403)

            user = User()
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            # Retrieve the user with the specified username 
            myusr = user.userget(username)
            
            if email == "": email = None
            if password == "": password = None

            myusr.userupdate(email, password)
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

class DeleteUser(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def deleteUser(request):
        try:
            user1 = request.user
            if user1.role != 'UserAdmin':
                return Response({'message': 'You don\'t have permission to update account'}, status=403)
            # Get the username from the request data
            user = User()
            username = request.data.get('username')
            # Retrieve the user with the specified username 
            myusr = user.userget(username)
            myusr.userdelete()
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class SearchUserView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def searchUser(request):
        # Check if user has permission to search user
        #if request.user.role != 'UserAdmin':
        #    raise PermissionDenied("You do not have permission to search user.")
        # Get prompt from request body
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'})
        
        result = User.usersearch(keyword)
        users = [u for u in result]
        data = [{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in users]
        return Response(data)

# User profile
class CreateProfile(APIView):
    Authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def createProfile(request):
        # Get the user data from the request
        username = request.data.get('username')
        name = request.data.get('name')
        date_of_birth = request.data.get('date_of_birth')

        user = User()
        profile = Profile()
        user_obj = user.userget(username)

        profile.profilecreate(user_obj, name, date_of_birth)

        # Return a response with the created profile data
        return Response(status=status.HTTP_200_OK)
    
class ViewProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['GET'])
    def viewProfile(request):
        # check if user has permission to view profiles
        if request.user.role != 'UserAdmin' and not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to view profiles.")

        result = Profile.profileall()
        profiles = [p for p in result]
        data = [{'id': p.id, 'username': p.user.username if p.user is not None else None, 'name': p.name, 'date_of_birth': p.date_of_birth} for p in profiles]
        return Response(data)
    
class SearchProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def searchProfile(request):
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'})
        
        result = Profile.profilesearch(keyword)
        profiles = [p for p in result]
        data = [{'id': p.id, 'username': p.user.username if p.user is not None else None, 'name': p.name, 'date_of_birth': p.date_of_birth} for p in profiles]
        return Response(data)
    
class DeleteProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def deleteProfile(request):
        try:
            user1 = request.user
            if user1.role != 'UserAdmin':
               return Response({'message': 'You don\'t have permission to update account'}, status=403)
            # Get the username from the request data
            profile = Profile()
            id = request.data.get('id')
            # Retrieve the user with the specified username 
            myprofile = profile.profileget(id)
            myprofile.profiledelete()
            return Response(status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'message': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

class UpdateProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def updateProfile(request):
        try:
            user1 = request.user
            if user1.role != 'UserAdmin':
                return Response({'message': 'You don\'t have permission to update account'}, status=403)

            profile = Profile()
            id = request.data.get('id')
            name = request.data.get('name')
            date_of_birth = request.data.get('date_of_birth')

            # Retrieve the user with the specified username 
            myprofile = profile.profileget(id)
            if name == "": name = None
            if date_of_birth == "": date_of_birth = None

            myprofile.profileupdate(name, date_of_birth)
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

# Movie
class AddMovie(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def addMov(request):
        # Check if user is a cinemaManager
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        # Get the user data from the request
        movie_title = request.data.get('movie_title')
        genre = request.data.get('genre')
        duration_str = request.data.get('duration')
        duration_convert = datetime.strptime(duration_str, '%H:%M:%S').time()
        duration = timedelta(hours=duration_convert.hour, minutes=duration_convert.minute, seconds=duration_convert.second)
        release_date = request.data.get('release_date')
        cast = request.data.get('cast')
        director = request.data.get('director')
        movie_description = request.data.get('movie_description')
        posterIMG = request.data.get('posterIMG')
        featureIMG = request.data.get('featureIMG')

        movie = Movie()
        movie.moviecreate(movie_title, genre, duration, release_date, cast, director, movie_description, posterIMG, featureIMG)

        # Return a response with the created profile data
        return Response(status=status.HTTP_200_OK)

class DeleteMovie(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def delMov(request):
        # Check if user is a cinemaManager
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        movie = Movie()
        movie_title = request.data.get('movie_title')
        try:
            movie_obj = movie.movieget(movie_title)
        except Movie.DoesNotExist:
            # If the movie does not exist, return 400 error
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Delete the movie from the database
        movie_obj.moviedelete()
        # Return a success response
        return Response(status=status.HTTP_200_OK)
    
class UpdateMovie(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])    
    def updateMov(request):
        
        # Check if user is a cinemaManager
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        movie = Movie()
        movie_title = request.data.get('movie_title')
        genre = request.data.get('genre')
        duration_str = request.data.get('duration')
        duration_convert = datetime.strptime(duration_str, '%H:%M:%S').time()
        duration = timedelta(hours=duration_convert.hour, minutes=duration_convert.minute, seconds=duration_convert.second)
        release_date = request.data.get('release_date')
        cast = request.data.get('cast')
        director = request.data.get('director')
        movie_description = request.data.get('movie_description')
        posterIMG = request.data.get('posterIMG')
        featureIMG = request.data.get('featureIMG')

        if genre == "":
            genre = None
        if duration == "":
            duration = None
        if release_date == "":
            release_date = None
        if cast == "":
            cast = None
        if director == "":
            director = None
        if movie_description == "":
            movie_description = None
        if posterIMG == "":
            posterIMG = None
        if featureIMG == "":
            featureIMG = None

        try:
            movie_obj = movie.movieget(movie_title)
        except Movie.DoesNotExist:
            # If the movie does not exist, return 404 error
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Update the movie from the database
        movie_obj.movieupdate(genre, duration, release_date, cast, director, movie_description, posterIMG, featureIMG)
        # Return a success response
        return Response(status=status.HTTP_200_OK)

class SearchMovie(APIView):
    permission_classes = [AllowAny]

    @api_view(['POST'])
    def SearchMov(request):
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'}, status=400)
        
        result = Movie.moviesearch(keyword)
        movies = [m for m in result]
        data = [{'movie_title': m.movie_title,
            'genre': m.genre,
            'duration': m.duration,
            'release_date': m.release_date,
            'cast': m.cast,
            'director': m.director,
            'movie_description': m.movie_description,
            'posterIMG': m.posterIMG,
            'featureIMG': m.featureIMG} for m in movies]
        return Response(data)
    
class ViewAllMovie(APIView):
    permission_classes = [AllowAny]

    @api_view(['GET'])
    def viewAllMovie(request):
        """
        Returns a list of all movie images
        """
        result = Movie.movieall()
        movies = [m for m in result]
        data = [{
            'id': m.id,
            'movie_title': m.movie_title,
            'genre': m.genre,
            'duration': m.duration,
            'release_date': m.release_date,
            'cast': m.cast,
            'director': m.director,
            'movie_description': m.movie_description,
            'posterIMG': m.posterIMG,
            'featureIMG': m.featureIMG} for m in movies]
        return Response(data)
    
# Cinema room
class AddCinemaRoom(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def addCR(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        # Get the user data from the request
        name = request.data.get('name')
        capacity = request.data.get('capacity')

        cr = CinemaRoom()
        cr.cinemaroomcreate(name, capacity)

        # Return a response with the created profile data
        return Response(status=status.HTTP_200_OK)

class UpdateCinemaRoom(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def updateCR(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Get the movie object to update
        name = request.data.get('name')
        capacity = request.data.get('capacity')
        cinemaRoom = CinemaRoom()
        try:
            cr = cinemaRoom.cinemaroomget(name)
        except CinemaRoom.DoesNotExist:
            return Response({'message': 'Cinema Room does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        if capacity == "":
            capacity = None
        cr.cinemaroomupdate(capacity)
        return Response(status=status.HTTP_200_OK)
        
class DeleteCinemaRoom(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def delCR(request):
         # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
           return Response(status=status.HTTP_403_FORBIDDEN)

        # Get the cinema room object to delete
        name = request.data.get('name')
        cinemaroom = CinemaRoom()
        try:
            cr = cinemaroom.cinemaroomget(name)
        except CinemaRoom.DoesNotExist:
            return Response({'message': 'Cinema Room does not exist'}, status=status.HTTP_404_NOT_FOUND)
        # Delete the cinema room
        cr.cinemaroomdelete()
        return Response(status=status.HTTP_200_OK)

class ViewAllCinemaRoom(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['GET'])   
    def viewAllCR(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)
        result = CinemaRoom.cinemaroomall()
        rooms = [r for r in result]
        data = [{'id': r.id, 'name': r.name, 'capacity': r.capacity} for r in rooms]
        return Response(data)
    
class SearchCinemaRoom(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def searchCR(request):
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'}, status=400)
        
        result = CinemaRoom.cinemaroomsearch(keyword)
        rooms = [cr for cr in result]
        data = [{'id': cr.id, 'name': cr.name, 'capacity': cr.capacity} for cr in rooms]
        return Response(data)

# Movie session
class AddMovieSession(APIView):
    Authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def addMS(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        movie = Movie()
        cinemaroom = CinemaRoom()
        moviesession = MovieSession()

        # Get movie, session date, cinema room and session time from request data
        movie_title = request.data['movie_title']
        session_date = request.data['session_date']
        cinema_room_name = request.data['cinema_room']
        session_time = request.data['session_time']

        # Retrieve movie and cinema room objects from the database
        try:
            mov = movie.movieget(movie_title)
            cr = cinemaroom.cinemaroomget(cinema_room_name)
        except (Movie.DoesNotExist, CinemaRoom.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check if session time is valid
        valid_session_times = ['8:30', '11:30', '14:00', '16:30', '17:50', '18:40', '19:30', '20:40', '21:10']
        if session_time not in valid_session_times:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Create new movie session
        moviesession.moviesessioncreate(mov, session_date, cr, session_time)

        return Response(status=status.HTTP_200_OK)
    
class ViewAllMovieSession(APIView):
    #Authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    @api_view(['GET'])
    def viewAllMS(request):
        # Check if user is a cinemaManager.
        #if request.user.role != 'CinemaManager':
        #   return Response(status=status.HTTP_403_FORBIDDEN)

        # Retrieve all movie sessions from the database
        result = MovieSession.moviesessionall()
        sessions = [s for s in result]
        data = [{'id': s.id, 'movie': s.movie.movie_title, 'session_date': s.session_date, 'session_time': s.session_time, 'cinema_room': s.cinema_room.name if s.cinema_room is not None else None} for s in sessions]
        return Response(data)
    
class DeleteMovieSession(APIView):
    Authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    #Search by movie session id
    def delMS(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)
        myid = request.data['id']  
        moviesession = MovieSession()   

        try:
            ms = moviesession.moviesessionget(myid)
            if not moviesession:
                raise MovieSession.DoesNotExist
        except MovieSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        ms.moviesessiondelete()
        return Response(status=status.HTTP_200_OK)
    
class UpdateMovieSession(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def updateMS(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Get the movie object to update
        id = request.data.get('id')
        session_date = request.data.get('session_date')
        session_time = request.data.get('session_time')
        moviesession = MovieSession()
        try:
            ms = moviesession.moviesessionget(id)
        except CinemaRoom.DoesNotExist:
            return Response({'message': 'Cinema Room does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        ms.moviesessionupdate(session_date, session_time)
        return Response(status=status.HTTP_200_OK)  

class RetrieveMovieSession(APIView):
    permission_classes = [AllowAny]

    @api_view(['POST'])
    def getMovieSession(request):
        try:
            movie_title = request.data['movie_title']
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            movie_obj = Movie().movieget(movie_title)
            result = MovieSession.moviesessionsearch(movie_obj)

            data = [{ 'id': str(m.id),
                      'movie': str(m.movie),
                      'session_date': str(m.session_date),
                      'cinema_room': str(m.cinema_room),
                      'session_time': m.session_time}for m in result]
            return Response(data)

        except (Movie.DoesNotExist, MovieSession.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)


  
class SearchMovieSession(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def searchMS(request):
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'})
        
        result = MovieSession.moviesessionsearch(keyword)
        sessions = [s for s in result]
        data = [{'id': s.id, 'movie': s.movie.movie_title, 'session_date': s.session_date, 'cinema_room': s.cinema_room.name if s.cinema_room is not None else None} for s in sessions]
        return Response(data)
    
class RetrieveMovieDetail(APIView):
    permission_classes = [AllowAny]
    
    @api_view(['POST'])
    def getMovDetail(request):

        movie = Movie()
        movie_title = request.data.get('movie_title')
        
        result = movie.moviesearch(movie_title)
        movies = [m for m in result]
        data = [{'movie_title': m.movie_title,
            'genre': m.genre,
            'duration': m.duration,
            'release_date': m.release_date,
            'cast': m.cast,
            'director': m.director,
            'movie_description': m.movie_description,
            'posterIMG': m.posterIMG,
            'featureIMG': m.featureIMG} for m in movies]

        return Response(data)

# FnB
class AddFnbs(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def addFnb(request):
        #Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Get the user data from the request
        menu = request.data.get('menu')
        menu_description = request.data.get('menu_description')
        price = request.data.get('price')
        menuIMG = request.data.get('menuIMG')

        fnb = FoodandBeverage()
        fnb.fnbcreate(menu, menu_description, price, menuIMG)

        # Return a response with the created fnb data
        return Response(status=status.HTTP_200_OK)

class ViewAllFnbs(APIView):
    permission_classes = [AllowAny]

    @api_view(['GET'])
    def viewAllFnb(request):

        """
        Returns a list of all movie images
        """
        result = FoodandBeverage.fnball()
        fnb = [f for f in result]
        data = [{
            'id': f.id,
            'menu': f.menu,
            'menu_description': f.menu_description,
            'price': f.price,
            'menuIMG': f.menuIMG} for f in fnb]
        return Response(data)
    
class UpdateFnbs(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def updateFnB(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        fnb = FoodandBeverage()
        id = request.data.get('id')
        price = request.data.get('price')

        if id == "":
            id = None
        if price == "":
            price = None
        
        try:
            fnb_obj = fnb.fnbget(id)
        except FoodandBeverage.DoesNotExist:
            # If the menu does not exist, return 400 error
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Delete the menu from the database
        fnb_obj.fnbupdate(price)
        # Return a success response
        return Response(status=status.HTTP_200_OK)

class DeleteFnbs(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def delFnB(request):
        # Check if user is a cinemaManager.
        if request.user.role != 'CinemaManager':
            return Response(status=status.HTTP_403_FORBIDDEN)

        fnb = FoodandBeverage()
        id = request.data.get('id')
        try:
            fnb_obj = fnb.fnbget(id)
        except FoodandBeverage.DoesNotExist:
            # If the movie does not exist, return 404 error
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the movie from the database
        fnb_obj.fnbdelete()
        # Return a success response
        return Response(status=status.HTTP_200_OK)

class SearchFnbs(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @api_view(['POST'])
    def searchFnB(request):
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'})
        
        result = FoodandBeverage.fnbsearch(keyword)
        fnb = [f for f in result]
        data = [{
            'id': f.id,
            'menu': f.menu,
            'menu_description': f.menu_description,
            'price': f.price,
            'menuIMG': f.menuIMG} for f in fnb]
        return Response(data)

# Booking
class AddBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def addBook(request):
        # Get the booking data from the request
        booking_owner_id = request.user.id
        booking_owner = User.objects.get(id=booking_owner_id)
        movie_session_id = request.data.get('movie_session')
        movie_session = MovieSession.objects.get(id=movie_session_id)
        ticket_type = request.data.get('ticket_type')
        seat_number = request.data.get('seat_number')

        #entity
        booking = MovieBooking()
        booking.movieBookingCreate(booking_owner, movie_session, ticket_type, seat_number)

        # Return a response with the created booking data
        return Response(status=status.HTTP_200_OK)

class ViewAllBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    #@api_view(['POST']) 
    @api_view(['GET'])
    def viewAllBook(request):
        # Check if user is authenticated.
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #frontend "auto input uuid" simulate get method
        #try:
        #    username = request.data['booking_owner']
        #except KeyError:
        #    return Response(status=status.HTTP_400_BAD_REQUEST)
        
        #alternate method 
        username = request.user.id

        result = MovieBooking.bookingall(username)
        moviebook = [m for m in result]
        data = [{
            'id':m.id,
            'booking_owner': m.booking_owner.username,
            'movie_title': m.movie_session.movie.movie_title,
            'movie_session_date': m.movie_session.session_date,
            'movie_session_time': m.movie_session.session_time,
            'ticket_type': m.ticket_type,
            'seat_number': m.seat_number} for m in moviebook]
        return Response(data)
    
#still in progress
class updateBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])    
    def updateBook(request):
        
        # Check if user is authenticated.
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        moviebook = MovieBooking()
        id = request.data.get('id')
        seat_number = request.data.get('seat_number')

        if id == "":
            id = None
        if seat_number == "":
            seat_number = None

        try:
            moviebook_obj = moviebook.bookingGet(id)
        except MovieBooking.DoesNotExist:
            # If the movie does not exist, return 404 error
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Delete the movie from the database
        moviebook_obj.movieBookingUpdate(seat_number)
        # Return a success response
        return Response(status=status.HTTP_200_OK)


class DeleteMovieBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def delBook(request):
        # Check if user is authenticated.
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        moviebook = MovieBooking()
        id = request.data.get('id')
        try:
            moviebook_obj = moviebook.bookingGet(id)
        except MovieBooking.DoesNotExist:
            # If the movie booking id does not exist, return 404 error
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the movie booking from the database
        moviebook_obj.bookingDelete()
        # Return a success response
        return Response(status=status.HTTP_200_OK)
    
#still in progress
class SearchMovieBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def SearchBook(request):
        # Check if user is authenticated.
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        #ticket type user required to manually select
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'})
        #id will be filled by frontend automatically
        #booking_owner_id = request.data.get('booking_owner', '')
        
        #alternate method 
        booking_owner_id = request.user.id
        
        result = MovieBooking.movieBookSearch(keyword, booking_owner_id)
        moviebook = [m for m in result]
        data = [{
            'movie_title': m.movie_session.movie.movie_title,
            'movie_session_date': m.movie_session.session_date,
            'movie_session_time': m.movie_session.session_time,
            'ticket_type': m.ticket_type,
            'seat_number': m.seat_number} for m in moviebook]
        return Response(data)
    
class CreateFnBBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def purchaseFnB(request):
        # Get the user data from the request
        booking_owner_id = request.user.id
        booking_owner = User.objects.get(id=booking_owner_id)
        menu_id = request.data.get('menu_id')
        menu = FoodandBeverage.objects.get(id=menu_id)
        
        FnB = FnBBooking()
        FnB.FnBBookingCreate(booking_owner, menu)

        # Return a response with the created booking data
        return Response(status=status.HTTP_200_OK)
    
class ViewPrePurchaseFnB(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def viewFnB(request):
        try:
            booking_id = request.data.get('id')
            booking = FnBBooking.objects.get(id=booking_id)
        except FnBBooking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            'booking_owner': booking.booking_owner.username,
            'menu': str(booking.menu),
            'menu_description': str(booking.menu.menu_description),
            'price': str(booking.menu.price),
            'menuIMG': str(booking.menu.menuIMG)
        }

        # Return a response with the booking data
        return Response(data, status=status.HTTP_200_OK)
            
    
class ViewFnBBooking(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    #@api_view(['POST'])
    @api_view(['GET'])
    def viewAllFnBBooking(request):

        #testing purposes
        #try:
        #    username = request.data['booking_owner']
        #except KeyError:
        #    return Response(status=status.HTTP_400_BAD_REQUEST)

        #alternate method 
        username = request.user.id

        result = FnBBooking.FnBBookingall(username)
        fnbBooking = [f for f in result]
        data = [{
            'id':f.id,
            'booking_owner': f.booking_owner.username,
            'menu': str(f.menu),
            'menu_description': str(f.menu.menu_description),
            'price': str(f.menu.price),
            'menuIMG': str(f.menu.menuIMG)} for f in fnbBooking]
        return Response(data)

class DeleteFnBBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def delFnBBooking(request):
        fnb = FnBBooking()
        id = request.data.get('id')
        try:
            fnbooking_obj = fnb.fnbbookingGet(id)

        except FnBBooking.DoesNotExist:
            # If the booking does not exist, return 400 error
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the FnB Booking from the database
        fnbooking_obj.FnBBookingDelete()

        # Return a success response
        return Response(status=status.HTTP_200_OK)
    
class UpdateFnBBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def updateFnBBooking(request):
        fnb = FnBBooking()
        id = request.data.get('id')
        menu = request.data.get('menu')

        if menu == "":
            menu = None

        # Update the FnB Booking
        try:
            fnbbook_id = fnb.fnbbookingGet(id)
        except FnBBooking.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # Update the FnB booking
        new_menu = FoodandBeverage.objects.get(menu = menu)
        fnbbook_id.fnbbookingUpdate(new_menu)
        # Return a success response
        return Response(status=status.HTTP_200_OK)
    
class SearchFnBBooking(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def searchFnBBooking(request):
        keyword = request.data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Please provide a keyword to search for'})
        
        #booking_owner_id = request.data.get('booking_owner', '')
        booking_owner_id = request.user.id

        result = FnBBooking.fnbbookingSearch(keyword, booking_owner_id)
        fnbbooking = [f for f in result]
        data = [{
            'booking_owner': f.booking_owner.username,
            'menu': str(f.menu),
            'menu_description': str(f.menu.menu_description),
            'price': str(f.menu.price),
            'menuIMG': str(f.menu.menuIMG)} for f in fnbbooking]
        return Response(data)



# ETC    
class HelperFunction(APIView):
    permission_classes = [AllowAny]
    
    #helper function
    @api_view(['GET'])
    def getUpComing(request):
        current_date = timezone.now().date()
        movies = Movie.objects.filter(release_date__gte=current_date)
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)
    
    @api_view(['POST'])
    def getFnB(request):
        fnbid = request.data.get('id')
        fnb = FoodandBeverage()
        try:
            fnbmain = fnb.fnbget(fnbid)
        except FoodandBeverage.DoesNotExist:
            return Response(status=404)
        data = {
            'id': fnbmain.id,
            'menu': fnbmain.menu,
            'menu_description': fnbmain.menu_description,
            'price': fnbmain.price,
            'menuIMG': fnbmain.menuIMG}
        
        return Response(data, status=200)

    @api_view(['GET'])
    def getNowShowing(request):
        current_date = timezone.now().date()
        movies = Movie.objects.filter(release_date__lt=current_date)
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

class DailyRevenueReport(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_view(['POST'])
    def genDailyRevenueReport(request):
         # Check if user is a Cinema Owner.
        if request.user.role != 'CinemaOwner':
           return Response(status=status.HTTP_403_FORBIDDEN)
        
        date = request.data.get('date')
        # Generate daily report
        report = Report.generate_daily_report(date)

            # Return response with report details
        response_data = {
            'report_id': report.id,
            'report_description': report.report_description,
        }

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
class WeeklyRevenueReport(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def genWeeklyRevenueReport(request):
         # Check if user is a Cinema Owner.
        if request.user.role != 'CinemaOwner':
           return Response(status=status.HTTP_403_FORBIDDEN)
        
        sdate = request.data.get('sdate')
        edate = request.data.get('edate')
        # Generate daily report
        report = Report.generate_weekly_report(sdate, edate)

            # Return response with report details
        response_data = {
            'report_id': report.id,
            'report_description': report.report_description,
        }

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
class MonthlyRevenueReport(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def genMonthlyRevenueReport(request):
         # Check if user is a Cinema Owner.
        if request.user.role != 'CinemaOwner':
           return Response(status=status.HTTP_403_FORBIDDEN)
        
        sdate = request.data.get('sdate')
        edate = request.data.get('edate')
        # Generate daily report
        report = Report.generate_monthly_report(sdate, edate)

            # Return response with report details
        response_data = {
            'report_id': report.id,
            'report_description': report.report_description,
        }

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
class DailyTicketReport(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def genDailyTicketReport(request):
         # Check if user is a Cinema Owner.
        if request.user.role != 'CinemaOwner':
           return Response(status=status.HTTP_403_FORBIDDEN)
        
        date = request.data.get('date')
        # Generate daily report
        report = Report.generate_daily_ticket_report(date)

            # Return response with report details
        response_data = {
            'report_id': report.id,
            'report_description': report.report_description,
        }

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
class WeeklyTicketReport(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def genWeeklyTicketReport(request):
         # Check if user is a Cinema Owner.
        if request.user.role != 'CinemaOwner':
           return Response(status=status.HTTP_403_FORBIDDEN)
        
        sdate = request.data.get('sdate')
        edate = request.data.get('edate')
        # Generate daily report
        report = Report.generate_weekly_ticket_report(sdate, edate)

            # Return response with report details
        response_data = {
            'report_id': report.id,
            'report_description': report.report_description,
        }

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
class MonthlyTicketReport(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def genMonthlyTicketReport(request):
         # Check if user is a Cinema Owner.
        if request.user.role != 'CinemaOwner':
           return Response(status=status.HTTP_403_FORBIDDEN)
        
        sdate = request.data.get('sdate')
        edate = request.data.get('edate')
        # Generate daily report
        report = Report.generate_monthly_ticket_report(sdate, edate)

            # Return response with report details
        response_data = {
            'report_id': report.id,
            'report_description': report.report_description,
        }

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
