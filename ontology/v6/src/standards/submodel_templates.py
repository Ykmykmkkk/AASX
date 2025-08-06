"""
Standard Submodel Templates based on Industry 4.0 specifications
Includes: Nameplate, TechnicalData, OperationalData, Documentation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .aas_models import (
    Submodel, Property, MultiLanguageProperty, SubmodelElementCollection,
    Reference, DataTypeDefXsd, LangString, ModelingKind, Key, KeyType,
    AdministrativeInformation
)


class SubmodelTemplates:
    """Factory class for creating standard submodels"""
    
    @classmethod
    def create_reference(cls, semantic_id: str) -> Reference:
        """Create a semantic reference"""
        return Reference.create_global_reference(semantic_id)
    
    @classmethod
    def create_nameplate_submodel(
        cls,
        serial_number: str,
        manufacturer_name: str,
        manufacturer_product_designation: str,
        **kwargs
    ) -> Submodel:
        """
        Create Digital Nameplate submodel based on ZVEI specification
        https://www.plattform-i40.de/IP/Redaktion/EN/Downloads/Publikation/Submodel_templates-Asset_Administration_Shell-digital_nameplate.html
        """
        nameplate = Submodel(
            id=f"urn:aas:Nameplate:{serial_number}",
            id_short="Nameplate",
            semantic_id=cls.create_reference("0173-1#01-AGJ677#002"),
            kind=ModelingKind.INSTANCE,
            administration=AdministrativeInformation(version="1", revision="0")
        )
        
        # Manufacturer information
        manufacturer_info = SubmodelElementCollection(
            id_short="ManufacturerInformation",
            semantic_id=cls.create_reference("0173-1#01-AGJ678#001")
        )
        
        manufacturer_info.value.extend([
            Property(
                id_short="ManufacturerName",
                value_type=DataTypeDefXsd.STRING,
                value=manufacturer_name,
                semantic_id=cls.create_reference("0173-1#02-AAO677#002")
            ),
            Property(
                id_short="ManufacturerProductDesignation",
                value_type=DataTypeDefXsd.STRING,
                value=manufacturer_product_designation,
                semantic_id=cls.create_reference("0173-1#02-AAW338#001")
            )
        ])
        
        # Add optional manufacturer properties
        if kwargs.get("manufacturer_article_number"):
            manufacturer_info.value.append(
                Property(
                    id_short="ManufacturerArticleNumber",
                    value_type=DataTypeDefXsd.STRING,
                    value=kwargs["manufacturer_article_number"],
                    semantic_id=cls.create_reference("0173-1#02-AAO676#003")
                )
            )
        
        if kwargs.get("manufacturer_order_code"):
            manufacturer_info.value.append(
                Property(
                    id_short="ManufacturerOrderCode",
                    value_type=DataTypeDefXsd.STRING,
                    value=kwargs["manufacturer_order_code"],
                    semantic_id=cls.create_reference("0173-1#02-AAO227#002")
                )
            )
        
        # Product information
        product_info = SubmodelElementCollection(
            id_short="ProductInformation",
            semantic_id=cls.create_reference("0173-1#01-AGJ679#001")
        )
        
        product_info.value.extend([
            Property(
                id_short="SerialNumber",
                value_type=DataTypeDefXsd.STRING,
                value=serial_number,
                semantic_id=cls.create_reference("0173-1#02-AAM556#002")
            ),
            Property(
                id_short="YearOfConstruction",
                value_type=DataTypeDefXsd.STRING,
                value=kwargs.get("year_of_construction", "2025"),
                semantic_id=cls.create_reference("0173-1#02-AAP906#001")
            )
        ])
        
        # Add optional product properties
        if kwargs.get("date_of_manufacture"):
            product_info.value.append(
                Property(
                    id_short="DateOfManufacture",
                    value_type=DataTypeDefXsd.DATE_TIME,
                    value=kwargs["date_of_manufacture"],
                    semantic_id=cls.create_reference("0173-1#02-AAR972#002")
                )
            )
        
        if kwargs.get("hardware_version"):
            product_info.value.append(
                Property(
                    id_short="HardwareVersion",
                    value_type=DataTypeDefXsd.STRING,
                    value=kwargs["hardware_version"],
                    semantic_id=cls.create_reference("0173-1#02-AAN270#002")
                )
            )
        
        if kwargs.get("software_version"):
            product_info.value.append(
                Property(
                    id_short="SoftwareVersion",
                    value_type=DataTypeDefXsd.STRING,
                    value=kwargs["software_version"],
                    semantic_id=cls.create_reference("0173-1#02-AAN737#002")
                )
            )
        
        nameplate.submodel_elements.extend([manufacturer_info, product_info])
        return nameplate
    
    @classmethod
    def create_technical_data_submodel(
        cls,
        serial_number: str,
        **properties
    ) -> Submodel:
        """
        Create Technical Data submodel
        """
        technical_data = Submodel(
            id=f"urn:aas:TechnicalData:{serial_number}",
            id_short="TechnicalData",
            semantic_id=cls.create_reference("0173-1#01-AFZ615#003"),
            kind=ModelingKind.INSTANCE,
            administration=AdministrativeInformation(version="1", revision="0")
        )
        
        # General Technical Properties
        general_properties = []
        
        # Power consumption
        if "power_consumption" in properties:
            general_properties.append(
                Property(
                    id_short="PowerConsumption",
                    value_type=DataTypeDefXsd.DECIMAL,
                    value=properties["power_consumption"],
                    semantic_id=cls.create_reference("0173-1#02-AAD001#001"),
                    description=[LangString("en", "Power consumption in kW")]
                )
            )
        
        # Weight
        if "weight" in properties:
            general_properties.append(
                Property(
                    id_short="Weight",
                    value_type=DataTypeDefXsd.DECIMAL,
                    value=properties["weight"],
                    semantic_id=cls.create_reference("0173-1#02-AAS627#002"),
                    description=[LangString("en", "Weight in kg")]
                )
            )
        
        # Dimensions
        if "dimensions" in properties:
            dimensions = properties["dimensions"]
            dimension_collection = SubmodelElementCollection(
                id_short="Dimensions",
                semantic_id=cls.create_reference("0173-1#01-AFZ621#001")
            )
            
            dimension_collection.value.extend([
                Property(
                    id_short="Length",
                    value_type=DataTypeDefXsd.DECIMAL,
                    value=dimensions.get("length", 0),
                    semantic_id=cls.create_reference("0173-1#02-AAB713#005"),
                    description=[LangString("en", "Length in mm")]
                ),
                Property(
                    id_short="Width",
                    value_type=DataTypeDefXsd.DECIMAL,
                    value=dimensions.get("width", 0),
                    semantic_id=cls.create_reference("0173-1#02-AAB714#005"),
                    description=[LangString("en", "Width in mm")]
                ),
                Property(
                    id_short="Height",
                    value_type=DataTypeDefXsd.DECIMAL,
                    value=dimensions.get("height", 0),
                    semantic_id=cls.create_reference("0173-1#02-AAB715#005"),
                    description=[LangString("en", "Height in mm")]
                )
            ])
            general_properties.append(dimension_collection)
        
        # Operating conditions
        if "operating_conditions" in properties:
            op_conditions = properties["operating_conditions"]
            op_collection = SubmodelElementCollection(
                id_short="OperatingConditions",
                semantic_id=cls.create_reference("0173-1#01-AFZ622#001")
            )
            
            if "temperature_min" in op_conditions:
                op_collection.value.append(
                    Property(
                        id_short="MinimumTemperature",
                        value_type=DataTypeDefXsd.DECIMAL,
                        value=op_conditions["temperature_min"],
                        semantic_id=cls.create_reference("0173-1#02-AAZ672#001"),
                        description=[LangString("en", "Minimum operating temperature in °C")]
                    )
                )
            
            if "temperature_max" in op_conditions:
                op_collection.value.append(
                    Property(
                        id_short="MaximumTemperature",
                        value_type=DataTypeDefXsd.DECIMAL,
                        value=op_conditions["temperature_max"],
                        semantic_id=cls.create_reference("0173-1#02-AAZ673#001"),
                        description=[LangString("en", "Maximum operating temperature in °C")]
                    )
                )
            
            if "humidity_max" in op_conditions:
                op_collection.value.append(
                    Property(
                        id_short="MaximumHumidity",
                        value_type=DataTypeDefXsd.DECIMAL,
                        value=op_conditions["humidity_max"],
                        semantic_id=cls.create_reference("0173-1#02-AAZ674#001"),
                        description=[LangString("en", "Maximum humidity in %")]
                    )
                )
            
            general_properties.append(op_collection)
        
        # Cooling requirements - Fixed: Add before creating collection
        if "requires_cooling_during_production" in properties:
            general_properties.append(
                Property(
                    id_short="requires_cooling_during_production",
                    value_type=DataTypeDefXsd.BOOLEAN,
                    value=str(properties["requires_cooling_during_production"]).lower(),
                    semantic_id=cls.create_reference("0173-1#02-AAZ675#001"),
                    description=[LangString("en", "Requires cooling during production")]
                )
            )
        
        # Create the collection with all properties
        if general_properties:
            general_collection = SubmodelElementCollection(
                id_short="GeneralTechnicalProperties",
                semantic_id=cls.create_reference("0173-1#01-AFZ624#001"),
                value=general_properties
            )
            technical_data.submodel_elements.append(general_collection)
        
        # Additional technical specifications
        if "technical_specifications" in properties:
            specs = properties["technical_specifications"]
            spec_collection = SubmodelElementCollection(
                id_short="TechnicalSpecifications",
                semantic_id=cls.create_reference("0173-1#01-AFZ625#001")
            )
            
            for key, value in specs.items():
                spec_collection.value.append(
                    Property(
                        id_short=key,
                        value_type=DataTypeDefXsd.STRING,
                        value=str(value)
                    )
                )
            
            technical_data.submodel_elements.append(spec_collection)
        
        return technical_data
    
    @classmethod
    def create_operational_data_submodel(
        cls,
        serial_number: str,
        machine_hours: float = 0.0,
        production_cycles: int = 0,
        **kwargs
    ) -> Submodel:
        """
        Create Operational Data submodel for runtime information
        """
        operational_data = Submodel(
            id=f"urn:aas:OperationalData:{serial_number}",
            id_short="OperationalData",
            semantic_id=cls.create_reference("0173-1#01-AFZ626#001"),
            kind=ModelingKind.INSTANCE,
            administration=AdministrativeInformation(version="1", revision="0")
        )
        
        # Operating metrics
        metrics = SubmodelElementCollection(
            id_short="OperatingMetrics",
            semantic_id=cls.create_reference("0173-1#01-AFZ627#001")
        )
        
        metrics.value.extend([
            Property(
                id_short="MachineHours",
                value_type=DataTypeDefXsd.DECIMAL,
                value=machine_hours,
                semantic_id=cls.create_reference("0173-1#02-AAI729#001"),
                description=[LangString("en", "Total machine operating hours")]
            ),
            Property(
                id_short="ProductionCycles",
                value_type=DataTypeDefXsd.INTEGER,
                value=production_cycles,
                semantic_id=cls.create_reference("0173-1#02-AAI730#001"),
                description=[LangString("en", "Total production cycles completed")]
            )
        ])
        
        # Add optional metrics
        if kwargs.get("last_maintenance_date"):
            metrics.value.append(
                Property(
                    id_short="LastMaintenanceDate",
                    value_type=DataTypeDefXsd.DATE_TIME,
                    value=kwargs["last_maintenance_date"],
                    semantic_id=cls.create_reference("0173-1#02-AAI731#001")
                )
            )
        
        if kwargs.get("error_count"):
            metrics.value.append(
                Property(
                    id_short="ErrorCount",
                    value_type=DataTypeDefXsd.INTEGER,
                    value=kwargs["error_count"],
                    semantic_id=cls.create_reference("0173-1#02-AAI732#001")
                )
            )
        
        operational_data.submodel_elements.append(metrics)
        
        # Current status
        if "current_status" in kwargs:
            status_collection = SubmodelElementCollection(
                id_short="CurrentStatus",
                semantic_id=cls.create_reference("0173-1#01-AFZ628#001")
            )
            
            status = kwargs["current_status"]
            status_collection.value.extend([
                Property(
                    id_short="OperatingState",
                    value_type=DataTypeDefXsd.STRING,
                    value=status.get("state", "IDLE"),
                    semantic_id=cls.create_reference("0173-1#02-AAI733#001")
                ),
                Property(
                    id_short="CurrentUtilization",
                    value_type=DataTypeDefXsd.DECIMAL,
                    value=status.get("utilization", 0.0),
                    semantic_id=cls.create_reference("0173-1#02-AAI734#001"),
                    description=[LangString("en", "Current utilization in percentage")]
                )
            ])
            
            if status.get("current_job"):
                status_collection.value.append(
                    Property(
                        id_short="CurrentJob",
                        value_type=DataTypeDefXsd.STRING,
                        value=status["current_job"],
                        semantic_id=cls.create_reference("0173-1#02-AAI735#001")
                    )
                )
            
            operational_data.submodel_elements.append(status_collection)
        
        # Job history
        if "job_history" in kwargs:
            history_collection = SubmodelElementCollection(
                id_short="JobHistory",
                semantic_id=cls.create_reference("0173-1#01-AFZ629#001")
            )
            
            for i, job in enumerate(kwargs["job_history"][:10]):  # Limit to last 10
                job_element = SubmodelElementCollection(
                    id_short=f"Job_{i+1}",
                    semantic_id=cls.create_reference("0173-1#01-AFZ630#001")
                )
                
                job_element.value.extend([
                    Property(
                        id_short="JobId",
                        value_type=DataTypeDefXsd.STRING,
                        value=job.get("job_id", f"JOB-{i+1}")
                    ),
                    Property(
                        id_short="ProductId",
                        value_type=DataTypeDefXsd.STRING,
                        value=job.get("product_id", "")
                    ),
                    Property(
                        id_short="StartTime",
                        value_type=DataTypeDefXsd.DATE_TIME,
                        value=job.get("start_time", "")
                    ),
                    Property(
                        id_short="EndTime",
                        value_type=DataTypeDefXsd.DATE_TIME,
                        value=job.get("end_time", "")
                    ),
                    Property(
                        id_short="Status",
                        value_type=DataTypeDefXsd.STRING,
                        value=job.get("status", "UNKNOWN")
                    )
                ])
                
                if job.get("error_code"):
                    job_element.value.append(
                        Property(
                            id_short="ErrorCode",
                            value_type=DataTypeDefXsd.STRING,
                            value=job["error_code"]
                        )
                    )
                
                history_collection.value.append(job_element)
            
            operational_data.submodel_elements.append(history_collection)
        
        return operational_data
    
    @classmethod
    def create_documentation_submodel(
        cls,
        serial_number: str,
        documents: List[Dict[str, Any]]
    ) -> Submodel:
        """
        Create Documentation submodel based on VDI 2770
        """
        documentation = Submodel(
            id=f"urn:aas:Documentation:{serial_number}",
            id_short="Documentation",
            semantic_id=cls.create_reference("0173-1#01-AFZ631#001"),
            kind=ModelingKind.INSTANCE,
            administration=AdministrativeInformation(version="1", revision="0")
        )
        
        # Document collection
        doc_collection = SubmodelElementCollection(
            id_short="Documents",
            semantic_id=cls.create_reference("0173-1#01-AFZ632#001")
        )
        
        for i, doc in enumerate(documents):
            doc_element = SubmodelElementCollection(
                id_short=f"Document_{i+1}",
                semantic_id=cls.create_reference("0173-1#01-AFZ633#001")
            )
            
            doc_element.value.extend([
                Property(
                    id_short="DocumentType",
                    value_type=DataTypeDefXsd.STRING,
                    value=doc.get("type", "Manual"),
                    semantic_id=cls.create_reference("0173-1#02-AAO734#001")
                ),
                MultiLanguageProperty(
                    id_short="Title",
                    value=[LangString("en", doc.get("title", f"Document {i+1}"))],
                    semantic_id=cls.create_reference("0173-1#02-AAO735#001")
                ),
                Property(
                    id_short="Version",
                    value_type=DataTypeDefXsd.STRING,
                    value=doc.get("version", "1.0"),
                    semantic_id=cls.create_reference("0173-1#02-AAO736#001")
                ),
                Property(
                    id_short="Date",
                    value_type=DataTypeDefXsd.DATE_TIME,
                    value=doc.get("date", datetime.now().isoformat()),
                    semantic_id=cls.create_reference("0173-1#02-AAO737#001")
                ),
                Property(
                    id_short="DocumentURL",
                    value_type=DataTypeDefXsd.ANY_URI,
                    value=doc.get("url", f"https://docs.example.com/{serial_number}/doc{i+1}"),
                    semantic_id=cls.create_reference("0173-1#02-AAO738#001")
                )
            ])
            
            if doc.get("format"):
                doc_element.value.append(
                    Property(
                        id_short="Format",
                        value_type=DataTypeDefXsd.STRING,
                        value=doc["format"],
                        semantic_id=cls.create_reference("0173-1#02-AAO739#001")
                    )
                )
            
            if doc.get("file_size"):
                doc_element.value.append(
                    Property(
                        id_short="FileSize",
                        value_type=DataTypeDefXsd.INTEGER,
                        value=doc["file_size"],
                        semantic_id=cls.create_reference("0173-1#02-AAO740#001"),
                        description=[LangString("en", "File size in bytes")]
                    )
                )
            
            doc_collection.value.append(doc_element)
        
        documentation.submodel_elements.append(doc_collection)
        return documentation