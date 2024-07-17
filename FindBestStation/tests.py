import logging
import responses
from django.test import TestCase
from django.urls import reverse

logger = logging.getLogger(__name__)

class ODsayAPITestCase(TestCase):
    @responses.activate
    def test_get_public_transport_info(self):
        logger.info("Starting test_get_public_transport_info...")
        
        # 더미 데이터 설정
        dummy_data = {
            "result": {
                "type": "dummy",
                "message": "This is dummy data for testing purposes."
            }
        }
        responses.add(
            responses.GET,
            'https://api.odsay.com/v1/api/searchPubTransPath',
            json=dummy_data,
            status=200
        )

        # API 호출
        response = self.client.get(reverse('get_public_transport_info'), data={
            'SX': '127.1054328',
            'SY': '37.3595963',
            'EX': '127.1102192',
            'EY': '37.3942435',
            'SearchType': '0'
        })
        
        logger.debug(f"API Response: {response.json()}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), dummy_data)