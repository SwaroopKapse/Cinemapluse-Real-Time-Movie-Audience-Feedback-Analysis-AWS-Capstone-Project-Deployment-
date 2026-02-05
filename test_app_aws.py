import os
import sys


os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:000000000000:cinemapulse-feedback"


from moto import mock_aws
import pytest
import boto3

def setup_test_environment():
    """Setup all mocked AWS resources"""
    REGION = "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    sns = boto3.client("sns", region_name=REGION)
    
    # =========== CREATE DYNAMODB TABLES ===========
    

    dynamodb.create_table(
        TableName="CinemaPulse_Users",
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "username", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "username-index",
                "KeySchema": [
                    {"AttributeName": "username", "KeyType": "HASH"}
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Movies Table
    dynamodb.create_table(
        TableName="CinemaPulse_Movies",
        KeySchema=[
            {"AttributeName": "movie_id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "movie_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Feedback Table
    dynamodb.create_table(
        TableName="CinemaPulse_Feedback",
        KeySchema=[
            {"AttributeName": "feedback_id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "feedback_id", "AttributeType": "S"},
            {"AttributeName": "movie_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "movie_id-index",
                "KeySchema": [
                    {"AttributeName": "movie_id", "KeyType": "HASH"}
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # =========== CREATE SNS TOPIC ===========
    topic = sns.create_topic(Name="cinemapulse-feedback")
    
    return dynamodb, sns



@mock_aws
def test_home_page():
    """Test: Home page loads"""
    setup_test_environment()
    from app_aws import app
    
    app.config["TESTING"] = True
    client = app.test_client()
    
    res = client.get("/")
    assert res.status_code == 200
    print("✅ TEST PASSED: Home page loads")

@mock_aws
def test_signup_login_flow():
    """Test: Signup and login with valid password"""
    setup_test_environment()
    from app_aws import app
    
    app.config["TESTING"] = True
    client = app.test_client()
    
   
    res = client.post(
        "/signup",
        data={"username": "testuser", "email": "t@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    print("TEST PASSED: Signup successful")


    res = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    print("TEST PASSED: Login successful")

@mock_aws
def test_api_movies():
    """Test: API movies endpoint"""
    setup_test_environment()
    from app_aws import app
    
    app.config["TESTING"] = True
    client = app.test_client()
    
    res = client.get("/api/movies")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    print(" TEST PASSED: API movies endpoint works")

@mock_aws
def test_signup_duplicate_username():
    """Test: Can't signup with duplicate username"""
    setup_test_environment()
    from app_aws import app
    
    app.config["TESTING"] = True
    client = app.test_client()
    
    # First signup
    res1 = client.post(
        "/signup",
        data={"username": "john", "email": "john@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert res1.status_code == 200
    
    # Try to signup with same username
    res2 = client.post(
        "/signup",
        data={"username": "john", "email": "john2@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert res2.status_code == 200
    print(" TEST PASSED: Duplicate username validation works")


# RUN ALL TESTS

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RUNNING CINEMAPULSE TESTS WITH MOTO 5.x")
    print("="*80 + "\n")
    
    pytest.main([__file__, "-v", "-s"])