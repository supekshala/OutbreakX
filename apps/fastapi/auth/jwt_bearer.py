# app/auth/jwt_bearer.py

from fastapi import Request, HTTPException, Depends, status
from jose import jwt, JWTError
from jose.utils import base64url_decode
import requests
import logging

logger = logging.getLogger(__name__)

# WSO2 Configuration
WSO2_ISSUER = "https://api.asgardeo.io/t/sixthflowresearch/oauth2/token"
JWKS_URL = "https://api.asgardeo.io/t/sixthflowresearch/oauth2/jwks"
CLIENT_ID = "p7yUpEFODgmOXRHX2Q6FtD9ROqIa"

# Cache JWKS keys
try:
    logger.info(f"Fetching JWKS from {JWKS_URL}")
    jwks_response = requests.get(JWKS_URL, timeout=10)
    jwks_response.raise_for_status()
    jwks = jwks_response.json()
    logger.info("Successfully fetched JWKS keys")
except requests.RequestException as e:
    logger.error(f"Failed to fetch JWKS: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch JWT validation keys"
    )

def get_public_key(token: str):
    try:
        headers = jwt.get_unverified_header(token)
        if "kid" not in headers:
            logger.error("JWT header missing 'kid'")
            raise HTTPException(status_code=401, detail="Invalid token: missing key ID")
            
        kid = headers["kid"]
        logger.debug(f"Looking for key with kid: {kid}")
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                try:
                    return jwt.construct_rsa_public_key(key)
                except Exception as e:
                    logger.error(f"Failed to construct public key: {str(e)}")
                    raise HTTPException(status_code=401, detail="Invalid token: key construction failed")
        
        logger.error(f"No matching key found for kid: {kid}")
        raise HTTPException(status_code=401, detail="Invalid token: no matching key")
        
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def decode_jwt(token: str):
    try:
        if not token:
            logger.error("No token provided")
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Log token header for debugging
        try:
            unverified_header = jwt.get_unverified_header(token)
            logger.debug(f"Token header: {unverified_header}")
        except Exception as e:
            logger.error(f"Failed to decode token header: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token format")
            
        logger.info(f"Decoding token with issuer: {WSO2_ISSUER}, audience: {CLIENT_ID}")
        
        try:
            key = get_public_key(token)
            logger.debug(f"Using public key: {key.public_numbers().n.bit_length()}-bit RSA key")
        except Exception as e:
            logger.error(f"Failed to get public key: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token: key error")
        
        # First, decode without verification to check the token structure
        try:
            unverified_payload = jwt.get_unverified_claims(token)
            logger.debug(f"Token payload (unverified): {unverified_payload}")
            
            # Log the actual issuer and audience from the token
            token_issuer = unverified_payload.get('iss', 'not provided')
            token_audience = unverified_payload.get('aud', 'not provided')
            logger.info(f"Token claims - iss: {token_issuer}, aud: {token_audience}")
            
        except Exception as e:
            logger.error(f"Failed to decode token payload: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token: malformed payload")
        
        # Now try to verify the token
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=CLIENT_ID,
                issuer=WSO2_ISSUER,
                options={
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True
                }
            )
            logger.info("Token validation successful")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTClaimsError as e:
            logger.error(f"Token claims error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token claims: {str(e)}")
            
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token validation failed")
