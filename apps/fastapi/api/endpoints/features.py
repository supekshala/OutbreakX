from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, status, Response
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
import logging
import traceback
import json
from sqlalchemy import text

from config.database import get_db
from models.project_feature import ProjectFeature
from schemas.geojson import GeoJSONFeatureCollection, FeatureResponse, GeoJSONFeature

router = APIRouter()
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

def features_equal(db_feature: ProjectFeature, new_feature: GeoJSONFeature) -> bool:
    """Compare a database feature with a new feature to check if they're equal."""
    try:
        # Convert database geometry to GeoJSON for comparison
        db_geom = to_shape(db_feature.geometry)
        db_geom_dict = shapely_mapping(db_geom)
        
        # Compare geometry type and coordinates
        if db_geom_dict['type'] != new_feature.geometry.type:
            return False
            
        # Compare coordinates (handle different precision levels)
        if db_geom_dict['coordinates'] != new_feature.geometry.coordinates:
            return False
            
        # Compare properties (excluding any internal fields)
        db_props = {k: v for k, v in db_feature.properties.items() 
                   if k not in ('created_at', 'updated_at')}
        new_props = new_feature.properties.dict(exclude={"type"}, exclude_none=True)
        
        return db_props == new_props
        
    except Exception as e:
        logger.warning(f"Error comparing features: {e}")
        return False

def find_matching_feature(feature: GeoJSONFeature, existing_features: List[ProjectFeature]) -> Optional[ProjectFeature]:
    """Find a matching feature in the existing features list."""
    for existing in existing_features:
        if features_equal(existing, feature):
            return existing
    return None

@router.put("/{project_id}/features", response_model=FeatureResponse)
async def update_project_features(
    project_id: int = Path(..., description="The ID of the project"),
    feature_collection: GeoJSONFeatureCollection = None,
    db: Session = Depends(get_db),
    # Uncomment and implement when authentication is ready
    # current_user: dict = Depends(get_current_user)
):
    """
    Update features for a specific project.
    
    Only updates features that have changed. Returns the number of features added, updated, or deleted.
    """
    logger.info(f"Received request to update features for project {project_id}")
    
    if not feature_collection or not feature_collection.features:
        # If no features provided, delete all features for this project
        deleted_count = db.query(ProjectFeature).filter(ProjectFeature.project_id == project_id).delete()
        db.commit()
        return {
            "status": "success", 
            "saved": 0, 
            "deleted": deleted_count, 
            "updated": 0, 
            "message": f"Deleted all {deleted_count} features for project {project_id}"
        }
    
    logger.info(f"Processing {len(feature_collection.features)} features")
    
    try:
        # Start a transaction
        db.begin()
        logger.debug("Database transaction started")
        
        # Get existing features for this project
        existing_features = db.query(ProjectFeature).filter(
            ProjectFeature.project_id == project_id
        ).all()
        
        logger.info(f"Found {len(existing_features)} existing features for project {project_id}")
        
        new_features = []
        processed_feature_ids = set()
        
        for idx, feature in enumerate(feature_collection.features, 1):
            try:
                logger.debug(f"Processing feature {idx}/{len(feature_collection.features)}")
                
                # Ensure properties exists and has a type
                if not hasattr(feature, 'properties') or feature.properties is None:
                    feature.properties = {}
                
                # Set default type if not provided
                feature_type = getattr(feature.properties, 'type', None)
                
                # If type is not set, try to determine it from geometry type
                if not feature_type and hasattr(feature.geometry, 'type'):
                    feature_type = feature.geometry.type.lower()
                    logger.info(f"Inferred feature type from geometry: {feature_type}")
                
                feature_type = feature_type or 'unknown'
                
                # Convert GeoJSON geometry to WKB
                try:
                    shapely_geom = shapely_shape(feature.geometry)
                    wkb_geom = from_shape(shapely_geom, srid=4326)
                except Exception as shape_error:
                    error_msg = f"Error processing geometry for feature {idx}: {str(shape_error)}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_msg
                    )
                
                # Create feature properties without 'type' since we store it separately
                properties = feature.properties.dict(exclude={"type"}, exclude_none=True) if feature.properties else {}
                
                # Create a temporary feature for comparison
                temp_feature = ProjectFeature(
                    project_id=project_id,
                    geometry=wkb_geom,
                    type=feature_type,
                    properties=properties
                )
                
                # Check if this feature matches an existing one
                matching_feature = find_matching_feature(feature, existing_features)
                
                if matching_feature:
                    # Feature exists and is unchanged
                    processed_feature_ids.add(matching_feature.id)
                    logger.debug(f"Feature {idx} matches existing feature {matching_feature.id}")
                else:
                    # Feature is new or changed - add to new features list
                    new_features.append(temp_feature)
                    logger.debug(f"Feature {idx} is new or modified")
                
            except HTTPException:
                db.rollback()
                raise
                
            except Exception as e:
                db.rollback()
                error_msg = f"Error processing feature {idx}: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
        
        # Find features to delete (those that weren't in the new collection)
        features_to_delete = [f for f in existing_features if f.id not in processed_feature_ids]
        deleted_count = len(features_to_delete)
        
        # Perform database operations
        if features_to_delete:
            feature_ids = [f.id for f in features_to_delete]
            db.query(ProjectFeature).filter(ProjectFeature.id.in_(feature_ids)).delete(synchronize_session=False)
            logger.info(f"Deleting {deleted_count} features that are no longer needed")
        
        # Add new features
        if new_features:
            db.bulk_save_objects(new_features)
            logger.info(f"Adding {len(new_features)} new or modified features")
        
        db.commit()
        
        # Calculate statistics
        unchanged_count = len(existing_features) - deleted_count
        
        return {
            "status": "success",
            "saved": len(new_features),
            "deleted": deleted_count,
            "unchanged": unchanged_count,
            "total": len(new_features) + unchanged_count,
            "message": (
                f"Updated project {project_id} with {len(new_features)} features. "
                f"Deleted {deleted_count} old features. "
                f"{unchanged_count} features unchanged."
            )
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


def db_feature_to_geojson(feature: ProjectFeature) -> Optional[Dict[str, Any]]:
    """
    Convert a database feature to GeoJSON format.
    
    Args:
        feature: The database feature to convert
        
    Returns:
        dict: GeoJSON feature as a dictionary, or None if conversion fails
    """
    try:
        logger.debug(f"Converting feature {getattr(feature, 'id', 'unknown')} to GeoJSON")
        
        # Check if geometry exists
        if not hasattr(feature, 'geometry') or feature.geometry is None:
            logger.error(f"Feature {getattr(feature, 'id', 'unknown')} has no geometry")
            return None
            
        # Convert WKB geometry to GeoJSON-compatible format
        try:
            geom = to_shape(feature.geometry)
            if geom is None:
                logger.error(f"Failed to convert geometry for feature {getattr(feature, 'id', 'unknown')}")
                return None
                
            # Convert geometry to GeoJSON format
            geom_json = mapping(geom)
        except Exception as geom_error:
            logger.error(f"Error converting geometry for feature {getattr(feature, 'id', 'unknown')}: {str(geom_error)}")
            return None
        
        # Prepare properties
        properties = {}
        if hasattr(feature, 'properties') and feature.properties:
            properties = dict(feature.properties)  # Convert SQLAlchemy JSONB to dict if needed
            
        # Add type to properties if it exists
        if hasattr(feature, 'type') and feature.type:
            properties['type'] = feature.type
        else:
            logger.warning(f"Feature {getattr(feature, 'id', 'unknown')} has no type")
            properties['type'] = 'unknown'
        
        # Create feature dictionary
        feature_dict = {
            'type': 'Feature',
            'geometry': geom_json,
            'properties': properties
        }
        
        # Add ID if it exists
        if hasattr(feature, 'id') and feature.id is not None:
            feature_dict['id'] = feature.id
            
        logger.debug(f"Successfully converted feature {getattr(feature, 'id', 'unknown')}")
        return feature_dict
        
    except Exception as e:
        logger.error(f"Unexpected error converting feature {getattr(feature, 'id', 'unknown')} to GeoJSON: {str(e)}")
        logger.error(traceback.format_exc())
        return None


@router.get("/{project_id}/features")
async def get_project_features(
    response: Response,
    project_id: int = Path(..., description="The ID of the project"),
    db: Session = Depends(get_db),
    # Uncomment and implement when authentication is ready
    # current_user: dict = Depends(get_current_user)
):
    """
    Get all features for a specific project in GeoJSON format.
    
    Returns a GeoJSON FeatureCollection containing all features for the project.
    """
    try:
        logger.info(f"Fetching features for project {project_id}")
        
        # First, verify the database connection
        try:
            db.execute(text("SELECT 1"))
            logger.debug("Database connection successful")
        except Exception as db_error:
            logger.error(f"Database connection error: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the database"
            )
        
        # Query all features for the project
        try:
            db_features = db.query(ProjectFeature).filter(
                ProjectFeature.project_id == project_id
            ).all()
            
            logger.info(f"Found {len(db_features)} features for project {project_id}")
            
            # Convert database features to GeoJSON features
            features = []
            for idx, db_feature in enumerate(db_features, 1):
                try:
                    logger.debug(f"Processing feature {idx}/{len(db_features)}")
                    feature_json = db_feature_to_geojson(db_feature)
                    if feature_json:
                        features.append(feature_json)
                    else:
                        logger.warning(f"Skipping feature {getattr(db_feature, 'id', 'unknown')} due to conversion error")
                except Exception as e:
                    logger.error(f"Error processing feature {getattr(db_feature, 'id', 'unknown')}: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
            
            # Create and return GeoJSON FeatureCollection
            result = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # Set response headers
            response.headers["Content-Type"] = "application/geo+json"
            return result
            
        except Exception as query_error:
            logger.error(f"Database query error: {str(query_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error querying features from database"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
