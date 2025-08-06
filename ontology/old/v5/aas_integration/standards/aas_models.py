"""
AAS (Asset Administration Shell) Metamodel 3.0 Implementation
Based on Industrial Digital Twin Association specifications
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime


class KeyType(Enum):
    """Types of keys for references"""
    GLOBAL_REFERENCE = "GlobalReference"
    FRAGMENT_REFERENCE = "FragmentReference"
    
    # Identifiable types
    ASSET_ADMINISTRATION_SHELL = "AssetAdministrationShell"
    CONCEPT_DESCRIPTION = "ConceptDescription"
    SUBMODEL = "Submodel"
    
    # Referable types
    SUBMODEL_ELEMENT_COLLECTION = "SubmodelElementCollection"
    SUBMODEL_ELEMENT_LIST = "SubmodelElementList"
    PROPERTY = "Property"
    MULTI_LANGUAGE_PROPERTY = "MultiLanguageProperty"
    RANGE = "Range"
    REFERENCE_ELEMENT = "ReferenceElement"
    DATA_ELEMENT = "DataElement"


class ModelingKind(Enum):
    """Modeling kind of an element"""
    TEMPLATE = "Template"
    INSTANCE = "Instance"


class AssetKind(Enum):
    """Kind of the asset"""
    TYPE = "Type"
    INSTANCE = "Instance"


class DataTypeDefXsd(Enum):
    """XSD data types for values"""
    BOOLEAN = "xs:boolean"
    INTEGER = "xs:integer"
    DECIMAL = "xs:decimal"
    STRING = "xs:string"
    DATE_TIME = "xs:dateTime"
    ANY_URI = "xs:anyURI"


@dataclass
class LangString:
    """Multi-language string"""
    language: str
    text: str


@dataclass
class Key:
    """Key for referencing elements"""
    type: KeyType
    value: str


@dataclass
class Reference:
    """Reference to another element"""
    type: str  # "GlobalReference" or "ModelReference"
    keys: List[Key]
    
    @classmethod
    def create_global_reference(cls, value: str) -> 'Reference':
        """Create a global reference with semantic ID"""
        return cls(
            type="GlobalReference",
            keys=[Key(type=KeyType.GLOBAL_REFERENCE, value=value)]
        )


@dataclass
class AdministrativeInformation:
    """Administrative information about an element"""
    version: Optional[str] = None
    revision: Optional[str] = None
    creator: Optional[Reference] = None
    template_id: Optional[str] = None


@dataclass
class Extension:
    """Extension for an element"""
    name: str
    value_type: Optional[DataTypeDefXsd] = None
    value: Optional[Any] = None
    refers_to: Optional[Reference] = None


@dataclass
class Qualifier:
    """Qualifier for an element"""
    type: str
    value_type: DataTypeDefXsd
    value: Optional[Any] = None
    value_id: Optional[Reference] = None


# Base classes

@dataclass
class Referable:
    """Base class for all referable elements"""
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)


@dataclass
class Identifiable:
    """Base class for all identifiable elements"""
    id: str
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    administration: Optional[AdministrativeInformation] = None


@dataclass
class HasSemantics:
    """Mixin for elements with semantic information"""
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)


@dataclass
class Qualifiable:
    """Mixin for qualifiable elements"""
    qualifiers: List[Qualifier] = field(default_factory=list)


@dataclass
class HasDataSpecification:
    """Mixin for elements with data specifications"""
    embedded_data_specifications: List[Reference] = field(default_factory=list)


# Core AAS classes

@dataclass
class AssetInformation:
    """Information about the asset"""
    asset_kind: AssetKind
    global_asset_id: Optional[str] = None
    specific_asset_ids: List[Dict[str, str]] = field(default_factory=list)
    asset_type: Optional[str] = None
    default_thumbnail: Optional[Dict[str, Any]] = None


@dataclass
class SubmodelElement:
    """Base class for all submodel elements"""
    # From Referable
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)


@dataclass
class Property:
    """Property element"""
    # From SubmodelElement/Referable
    id_short: str
    value_type: DataTypeDefXsd
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # Own fields
    value: Optional[Any] = None
    value_id: Optional[Reference] = None


@dataclass
class MultiLanguageProperty:
    """Multi-language property element"""
    # From SubmodelElement/Referable
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # Own fields
    value: Optional[List[LangString]] = None
    value_id: Optional[Reference] = None


@dataclass
class Range:
    """Range element"""
    # From SubmodelElement/Referable
    id_short: str
    value_type: DataTypeDefXsd
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # Own fields
    min: Optional[Any] = None
    max: Optional[Any] = None


@dataclass
class ReferenceElement:
    """Reference element"""
    # From SubmodelElement/Referable
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # Own fields
    value: Optional[Reference] = None


@dataclass
class SubmodelElementCollection:
    """Collection of submodel elements"""
    # From SubmodelElement/Referable
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # Own fields
    value: List[Any] = field(default_factory=list)  # Changed to Any to avoid circular reference


@dataclass
class SubmodelElementList:
    """Ordered list of submodel elements"""
    # From SubmodelElement/Referable
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # Own fields
    order_relevant: bool = True
    semantic_id_list_element: Optional[Reference] = None
    value_type_list_element: Optional[DataTypeDefXsd] = None
    value: List[Any] = field(default_factory=list)  # Changed to Any to avoid circular reference


@dataclass
class Submodel:
    """Submodel containing a structured set of SubmodelElements"""
    # From Identifiable
    id: str
    id_short: str
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    administration: Optional[AdministrativeInformation] = None
    # From HasSemantics
    semantic_id: Optional[Reference] = None
    supplemental_semantic_ids: List[Reference] = field(default_factory=list)
    # From Qualifiable
    qualifiers: List[Qualifier] = field(default_factory=list)
    # From HasDataSpecification
    embedded_data_specifications: List[Reference] = field(default_factory=list)
    # Own fields
    kind: ModelingKind = ModelingKind.INSTANCE
    submodel_elements: List[Any] = field(default_factory=list)  # Changed to Any to avoid circular reference


@dataclass
class AssetAdministrationShell:
    """Asset Administration Shell"""
    # From Identifiable
    id: str
    id_short: str
    asset_information: AssetInformation
    category: Optional[str] = None
    display_name: Optional[List[LangString]] = None
    description: Optional[List[LangString]] = None
    extensions: List[Extension] = field(default_factory=list)
    administration: Optional[AdministrativeInformation] = None
    # From HasDataSpecification
    embedded_data_specifications: List[Reference] = field(default_factory=list)
    # Own fields
    submodels: List[Reference] = field(default_factory=list)
    derived_from: Optional[Reference] = None


# Utility functions for JSON serialization

def serialize_reference(ref: Reference) -> Dict[str, Any]:
    """Serialize a Reference to JSON"""
    return {
        "type": ref.type,
        "keys": [{"type": k.type.value, "value": k.value} for k in ref.keys]
    }


def serialize_lang_string(ls: LangString) -> Dict[str, str]:
    """Serialize a LangString to JSON"""
    return {"language": ls.language, "text": ls.text}


def serialize_property(prop: Property) -> Dict[str, Any]:
    """Serialize a Property to JSON"""
    result = {
        "modelType": "Property",
        "idShort": prop.id_short,
        "valueType": prop.value_type.value,
    }
    if prop.value is not None:
        result["value"] = str(prop.value)
    if prop.semantic_id:
        result["semanticId"] = serialize_reference(prop.semantic_id)
    if prop.description:
        result["description"] = [serialize_lang_string(d) for d in prop.description]
    return result


def serialize_submodel_element_collection(
    collection: SubmodelElementCollection
) -> Dict[str, Any]:
    """Serialize a SubmodelElementCollection to JSON"""
    result = {
        "modelType": "SubmodelElementCollection",
        "idShort": collection.id_short,
        "value": []
    }
    
    for element in collection.value:
        if isinstance(element, Property):
            result["value"].append(serialize_property(element))
        elif isinstance(element, SubmodelElementCollection):
            result["value"].append(serialize_submodel_element_collection(element))
        elif isinstance(element, MultiLanguageProperty):
            result["value"].append({
                "modelType": "MultiLanguageProperty",
                "idShort": element.id_short,
                "value": [serialize_lang_string(v) for v in element.value] if element.value else []
            })
    
    if collection.semantic_id:
        result["semanticId"] = serialize_reference(collection.semantic_id)
    if collection.description:
        result["description"] = [serialize_lang_string(d) for d in collection.description]
    
    return result


def serialize_submodel(submodel: Submodel) -> Dict[str, Any]:
    """Serialize a Submodel to JSON"""
    result = {
        "modelType": "Submodel",
        "id": submodel.id,
        "idShort": submodel.id_short,
        "kind": submodel.kind.value,
        "submodelElements": []
    }
    
    for element in submodel.submodel_elements:
        if isinstance(element, Property):
            result["submodelElements"].append(serialize_property(element))
        elif isinstance(element, SubmodelElementCollection):
            result["submodelElements"].append(serialize_submodel_element_collection(element))
        elif isinstance(element, MultiLanguageProperty):
            result["submodelElements"].append({
                "modelType": "MultiLanguageProperty",
                "idShort": element.id_short,
                "value": [serialize_lang_string(v) for v in element.value] if element.value else []
            })
    
    if submodel.semantic_id:
        result["semanticId"] = serialize_reference(submodel.semantic_id)
    if submodel.description:
        result["description"] = [serialize_lang_string(d) for d in submodel.description]
    if submodel.administration:
        result["administration"] = {
            "version": submodel.administration.version,
            "revision": submodel.administration.revision
        }
    
    return result


def serialize_aas(shell: AssetAdministrationShell) -> Dict[str, Any]:
    """Serialize an AssetAdministrationShell to JSON"""
    result = {
        "modelType": "AssetAdministrationShell",
        "id": shell.id,
        "idShort": shell.id_short,
        "assetInformation": {
            "assetKind": shell.asset_information.asset_kind.value,
        }
    }
    
    if shell.asset_information.global_asset_id:
        result["assetInformation"]["globalAssetId"] = shell.asset_information.global_asset_id
    
    if shell.asset_information.specific_asset_ids:
        result["assetInformation"]["specificAssetIds"] = shell.asset_information.specific_asset_ids
    
    if shell.description:
        result["description"] = [serialize_lang_string(d) for d in shell.description]
    
    if shell.administration:
        result["administration"] = {
            "version": shell.administration.version,
            "revision": shell.administration.revision
        }
    
    if shell.submodels:
        result["submodels"] = [serialize_reference(ref) for ref in shell.submodels]
    
    return result