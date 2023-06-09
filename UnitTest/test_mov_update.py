from core.models import User, Movie
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from api.checklist import *
from django.urls import reverse
from datetime import timedelta, date
import base64

class TestMovUpdate(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # create an admin user
        self.admin_user = User.objects.create_user(username='admin', password='password', email='ad1@gmail.com', role='CinemaManager')
        self.admin_user.save()
        # log in the admin user
        response = self.client.post('/login/', {'username': 'admin', 'password': 'password'})
        self.admin_token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        if update_mov:
            self.url = reverse('updateMov')
        #setup movie img
        with open('UnitTest/testimg.png', 'rb') as f:
            img_data = f.read()
        self.base64_img_data = base64.b64encode(img_data).decode('utf-8')
        with open('UnitTest/BBB.jpg', 'rb') as f:
            img_data = f.read()
        self.base64_img_data1 = base64.b64encode(img_data).decode('utf-8')
        #setup movie object
        self.movie_obj = Movie.objects.create(movie_title='test', duration=timedelta(hours=1, minutes=30), 
                                              release_date=date(2022, 5, 1), cast='John Doe',director='Jane Smith',
                                              movie_description='A test movie',
                                              posterIMG = self.base64_img_data,
                                            featureIMG = self.base64_img_data)

    def test_update_mov(self):
        if not update_mov:
            return
        
        payload = {
            'movie_title': 'test', 
            'genre': 'Comedy',
            'duration' : timedelta(hours=1, minutes=30), 
            'release_date' :date(2022, 5, 1), 
            'cast' : 'John Doe Anderson',
            'director' :'Jane Smith, Johnny Dang',
            'movie_description' : 'A test movie updated',
            'posterIMG': self.base64_img_data1,
            'featureIMG': self.base64_img_data1
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("\nUnit test updateMov_1 passed")

    def test_update_mov_no_permission(self):
        if not update_mov:
            return
        self.usertest = User.objects.create_user(username='testuser', password='password', email='testusr@gmail.com', role='Customer')
        self.usertest.save()

        response = self.client.post('/login/', {'username': 'testuser', 'password': 'password'})
        self.test_token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.test_token)

        payload = {
            'movie_title': 'test', 
            'genre': 'Comedy',
            'duration' : timedelta(hours=1, minutes=30), 
            'release_date' :date(2022, 5, 1), 
            'cast' : 'John Doe Anderson',
            'director' :'Jane Smith, Johnny Dang',
            'movie_description' : 'A test movie updated',
            'posterIMG': self.base64_img_data1,
            'featureIMG': self.base64_img_data1
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("\nUnit test updateMov_2 passed")
    
