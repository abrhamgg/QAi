import pytest
from unittest.mock import Mock, patch
from boto3.dynamodb.conditions import Key
from services.dynamo_service import DynamoService 

@pytest.fixture
def dynamo_service():
    with patch('boto3.resource') as mock_resource:
        mock_table = Mock()
        mock_resource.return_value.Table.return_value = mock_table
        service = DynamoService()
        yield service, mock_table

def test_create_table(dynamo_service):
    service, mock_table = dynamo_service
    service.dynamodb.create_table = Mock()
    service.create_table()
    service.dynamodb.create_table.assert_called_once()

def test_get_all_data(dynamo_service):
    service, mock_table = dynamo_service
    mock_table.scan.return_value = {'Items': [{'created_at': '2024-01-01 12:00 PM'}]}
    result = service.get_all_data()
    assert isinstance(result, list)
    assert len(result) > 0

def test_get_all_by_columns(dynamo_service):
    service, mock_table = dynamo_service
    mock_table.scan.return_value = {'Items': [{'created_at': '2024-01-01 12:00 PM'}]}
    result = service.get_all_by_columns(location_id='123')
    assert isinstance(result, list)
    assert len(result) > 0

def test_get_item_by_contact_id(dynamo_service):
    service, mock_table = dynamo_service
    mock_table.get_item.return_value = {'Item': {'contact_id': '123'}}
    result = service.get_item_by_contact_id('123')
    assert result == {'contact_id': '123'}

def test_add_item(dynamo_service):
    service, mock_table = dynamo_service
    service.add_item({'contact_id': '123'})
    mock_table.put_item.assert_called_once_with(Item={'contact_id': '123'})

def test_delete_item_by_contact_id(dynamo_service):
    service, mock_table = dynamo_service
    result = service.delete_item_by_contact_id('123', 'location_id')
    assert result == True
    mock_table.delete_item.assert_called_once_with(Key={'contact_id': '123'})

def test_update_item_by_contact_id(dynamo_service):
    service, mock_table = dynamo_service
    result = service.update_item_by_contact_id('123', {'name': 'John'})
    assert result == True
    mock_table.update_item.assert_called_once()
    
    
if __name__ == "__main__":
    pytest.main(["-v", "test_dynamo_service.py"])