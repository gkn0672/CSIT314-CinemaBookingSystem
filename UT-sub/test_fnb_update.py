from core.models import User, FoodandBeverage
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from api.checklist import *
from django.urls import reverse
from datetime import timedelta, date
import base64

class TestUpdateFnb(APITestCase):

    def setUp(self):
        self.client = APIClient()
        # create an admin user
        self.admin_user = User.objects.create_user(username='admin', password='password', email='ad1@gmail.com', role='CinemaManager')
        self.admin_user.save()
        # log in the admin user
        response = self.client.post('/login/', {'username': 'admin', 'password': 'password'})
        self.admin_token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        if update_fnb:
            self.url = reverse('updateFnb')
        #setup movie img
        with open('UnitTest/testimg.png', 'rb') as f:
            img_data = f.read()
        self.base64_img_data = base64.b64encode(img_data).decode('utf-8')
        with open('UnitTest/BBB.jpg', 'rb') as f:
            img_data = f.read()
        self.base64_img_data1 = base64.b64encode(img_data).decode('utf-8')
        #setup Fnb
        self.fnb_obj = FoodandBeverage.objects.create(menu= 'test',
            menu_description= 'test',
            price= 10.23,
            menuIMG= self.base64_img_data )
        self.fnb_obj.save()

    def test_update_fnb_success(self):
        if not update_fnb:
            return

        payload = {
            'id': self.fnb_obj.id,
            'price': 99.99,
            'is_available': ""
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fnb_result = FoodandBeverage.objects.filter(menu='test').first()
        self.assertEqual(fnb_result.price, 99.99)
        print("\nUnit test updateFnb_1 passed")
        

    def test_update_fnb_unauthorized(self):
        if not update_fnb:
            return
        self.usertest = User.objects.create_user(username='testuser', password='password', email='testusr@gmail.com', role='Customer')
        self.usertest.save()
        response = self.client.post('/login/', {'username': 'testuser', 'password': 'password'})
        self.test_token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.test_token)

        payload = {
            'id': self.fnb_obj.id,
            'price': 99.99,
            'is_available': ""
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        fnb_result = FoodandBeverage.objects.filter(menu='test').first()
        self.assertEqual(fnb_result.price, 10.23)
        print("\nUnit test updateFnb_2 passed")