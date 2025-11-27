#!/usr/bin/env python3
"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
import re

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class CreateCharacterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\s]+$', v):
            raise ValueError('Character name can only contain letters, numbers, underscores, and spaces')
        return v.strip()

class StartCombatRequest(BaseModel):
    character_id: str
    opponent_id: Optional[str] = None
    enemy_id: Optional[str] = None

class CombatActionRequest(BaseModel):
    combat_id: str
    action_type: str = Field(..., pattern='^(attack|ability|defend)$')
    ability_id: Optional[str] = None
    target: Optional[str] = None

class EquipmentUpgradeRequest(BaseModel):
    character_id: str
    item_id: str
    new_level: int = Field(..., ge=1, le=100)

class EquipmentRerollRequest(BaseModel):
    character_id: str
    item_id: str

class AllocateSkillsRequest(BaseModel):
    character_id: str
    skill_allocations: Dict[str, int] = Field(..., description="Dictionary of stat_name: points")

class CreateFeedbackRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    character_id: Optional[str] = None

class BuyStoreItemRequest(BaseModel):
    character_id: str
    item_id: str

class SellItemRequest(BaseModel):
    character_id: str
    item_id: str

class UpdateStanceRequest(BaseModel):
    stance: str = Field(..., pattern='^(offensive|defensive|balanced)$')

