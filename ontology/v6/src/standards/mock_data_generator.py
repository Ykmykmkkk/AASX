"""
Mock Data Generator for AAS Test Environment
Generates realistic industrial equipment and production data
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .aas_models import (
    AssetAdministrationShell, AssetInformation, AssetKind,
    Reference, Key, KeyType, AdministrativeInformation,
    serialize_aas, serialize_submodel
)
from .submodel_templates import SubmodelTemplates


class MockDataGenerator:
    """Generate mock AAS data for testing"""
    
    def __init__(self, output_dir: str = "aas_integration/mock_data"):
        self.output_dir = output_dir
        self.templates = SubmodelTemplates()
        
    def generate_all_data(self):
        """Generate all mock data"""
        print("🔄 Generating mock AAS data...")
        
        # Create output directories
        os.makedirs(os.path.join(self.output_dir, "shells"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "submodels"), exist_ok=True)
        
        # Generate data
        machines = self.generate_machine_shells()
        products = self.generate_product_shells()
        job_history = self.generate_job_history()
        
        # Save summary
        summary = {
            "generated_at": datetime.now().isoformat(),
            "machines": len(machines),
            "products": len(products),
            "jobs": len(job_history),
            "test_date": "2025-07-17"
        }
        
        with open(os.path.join(self.output_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Generated {len(machines)} machines, {len(products)} products, {len(job_history)} jobs")
        return summary
    
    def generate_machine_shells(self) -> List[Dict[str, Any]]:
        """Generate machine Asset Administration Shells"""
        machines = [
            # CNC Machines (cooling required)
            {
                "id": "CNC001",
                "name": "DMG MORI DMU 50",
                "manufacturer": "DMG MORI",
                "model": "DMU 50",
                "serial": "DMGMORI-DMU50-2024-001",
                "cooling_required": True,
                "power_consumption": 15.5,
                "weight": 3500,
                "dimensions": {"length": 2200, "width": 2000, "height": 2700},
                "operating_conditions": {
                    "temperature_min": 15,
                    "temperature_max": 35,
                    "humidity_max": 80
                },
                "machine_hours": 4523.5,
                "production_cycles": 12847,
                "last_maintenance": "2025-06-15T10:00:00Z"
            },
            {
                "id": "CNC002",
                "name": "HAAS VF-2SS",
                "manufacturer": "HAAS Automation",
                "model": "VF-2SS",
                "serial": "HAAS-VF2SS-2024-002",
                "cooling_required": True,
                "power_consumption": 20.0,
                "weight": 4200,
                "dimensions": {"length": 2438, "width": 2159, "height": 2769},
                "operating_conditions": {
                    "temperature_min": 10,
                    "temperature_max": 40,
                    "humidity_max": 75
                },
                "machine_hours": 3211.2,
                "production_cycles": 9833,
                "last_maintenance": "2025-07-01T14:00:00Z"
            },
            # CNC Machine (self-cooling)
            {
                "id": "CNC003",
                "name": "Mazak VARIAXIS i-700",
                "manufacturer": "Yamazaki Mazak",
                "model": "VARIAXIS i-700",
                "serial": "MAZAK-VI700-2024-003",
                "cooling_required": False,  # Has integrated cooling
                "power_consumption": 18.0,
                "weight": 5800,
                "dimensions": {"length": 3000, "width": 3100, "height": 3200},
                "operating_conditions": {
                    "temperature_min": 5,
                    "temperature_max": 45,
                    "humidity_max": 85
                },
                "machine_hours": 1876.8,
                "production_cycles": 5442,
                "last_maintenance": "2025-06-20T09:00:00Z"
            },
            # 3D Printer
            {
                "id": "3DP001",
                "name": "Stratasys F370",
                "manufacturer": "Stratasys",
                "model": "F370",
                "serial": "STRAT-F370-2024-001",
                "cooling_required": False,
                "power_consumption": 2.5,
                "weight": 227,
                "dimensions": {"length": 1626, "width": 864, "height": 1626},
                "operating_conditions": {
                    "temperature_min": 15,
                    "temperature_max": 30,
                    "humidity_max": 70
                },
                "machine_hours": 987.3,
                "production_cycles": 342,
                "last_maintenance": "2025-05-10T11:00:00Z"
            },
            # Assembly Robot
            {
                "id": "ASM001",
                "name": "KUKA KR 10 R1100",
                "manufacturer": "KUKA",
                "model": "KR 10 R1100",
                "serial": "KUKA-KR10-2024-001",
                "cooling_required": False,
                "power_consumption": 3.0,
                "weight": 54,
                "dimensions": {"length": 1100, "width": 1100, "height": 1400},
                "operating_conditions": {
                    "temperature_min": 5,
                    "temperature_max": 45,
                    "humidity_max": 90
                },
                "machine_hours": 6234.1,
                "production_cycles": 45123,
                "last_maintenance": "2025-07-05T16:00:00Z"
            }
        ]
        
        # Generate AAS for each machine
        for machine in machines:
            shell = self._create_machine_shell(machine)
            submodels = self._create_machine_submodels(machine)
            
            # Save shell
            shell_json = serialize_aas(shell)
            with open(os.path.join(self.output_dir, "shells", f"{machine['id']}.json"), "w") as f:
                json.dump(shell_json, f, indent=2)
            
            # Save submodels
            for submodel in submodels:
                submodel_json = serialize_submodel(submodel)
                with open(os.path.join(self.output_dir, "submodels", f"{machine['id']}_{submodel.id_short}.json"), "w") as f:
                    json.dump(submodel_json, f, indent=2)
        
        return machines
    
    def generate_product_shells(self) -> List[Dict[str, Any]]:
        """Generate product Asset Administration Shells"""
        products = [
            {
                "id": "Product-A1",
                "name": "Precision Gear",
                "type": "Gear",
                "material": "Steel",
                "requires_cooling": False,
                "dimensions": {"diameter": 150, "thickness": 30},
                "weight": 2.5,
                "tolerance": 0.01,
                "batch_size": 100
            },
            {
                "id": "Product-B1",
                "name": "Aluminum Housing",
                "type": "Housing",
                "material": "Aluminum 6061",
                "requires_cooling": True,  # Aluminum requires cooling
                "dimensions": {"length": 200, "width": 150, "height": 80},
                "weight": 1.8,
                "tolerance": 0.05,
                "batch_size": 50
            },
            {
                "id": "Product-C1",
                "name": "Titanium Component",
                "type": "Aerospace Component",
                "material": "Titanium Grade 5",
                "requires_cooling": True,  # Titanium requires cooling
                "dimensions": {"length": 300, "width": 100, "height": 50},
                "weight": 3.2,
                "tolerance": 0.02,
                "batch_size": 20
            },
            {
                "id": "Product-D1",
                "name": "Plastic Prototype",
                "type": "Prototype",
                "material": "ABS Plastic",
                "requires_cooling": False,
                "dimensions": {"length": 120, "width": 80, "height": 60},
                "weight": 0.3,
                "tolerance": 0.1,
                "batch_size": 10
            }
        ]
        
        # Generate AAS for each product
        for product in products:
            shell = self._create_product_shell(product)
            submodels = self._create_product_submodels(product)
            
            # Save shell
            shell_json = serialize_aas(shell)
            with open(os.path.join(self.output_dir, "shells", f"{product['id']}.json"), "w") as f:
                json.dump(shell_json, f, indent=2)
            
            # Save submodels
            for submodel in submodels:
                submodel_json = serialize_submodel(submodel)
                with open(os.path.join(self.output_dir, "submodels", f"{product['id']}_{submodel.id_short}.json"), "w") as f:
                    json.dump(submodel_json, f, indent=2)
        
        return products
    
    def generate_job_history(self) -> List[Dict[str, Any]]:
        """Generate job history with cooling-related failures"""
        base_date = datetime(2025, 7, 17, 8, 0, 0)  # Start at 8 AM
        
        jobs = [
            # Failed jobs (cooling-related)
            {
                "job_id": "JOB-001",
                "machine_id": "CNC002",
                "product_id": "Product-B1",
                "start_time": base_date.isoformat() + "Z",
                "end_time": (base_date + timedelta(minutes=45)).isoformat() + "Z",
                "status": "FAILED",
                "error_code": "cooling_system_error",
                "error_message": "Cooling system malfunction detected",
                "temperature_at_failure": 85.5
            },
            {
                "job_id": "JOB-002",
                "machine_id": "CNC001",
                "product_id": "Product-C1",
                "start_time": (base_date + timedelta(hours=2)).isoformat() + "Z",
                "end_time": (base_date + timedelta(hours=2, minutes=30)).isoformat() + "Z",
                "status": "FAILED",
                "error_code": "temperature_exceeded",
                "error_message": "Maximum temperature threshold exceeded",
                "temperature_at_failure": 92.3
            },
            {
                "job_id": "JOB-003",
                "machine_id": "CNC002",
                "product_id": "Product-B1",
                "start_time": (base_date + timedelta(hours=4)).isoformat() + "Z",
                "end_time": (base_date + timedelta(hours=4, minutes=15)).isoformat() + "Z",
                "status": "FAILED",
                "error_code": "coolant_flow_insufficient",
                "error_message": "Insufficient coolant flow rate",
                "coolant_flow_rate": 2.3  # L/min (normal: >5)
            },
            # Successful jobs
            {
                "job_id": "JOB-004",
                "machine_id": "CNC003",
                "product_id": "Product-A1",
                "start_time": (base_date + timedelta(hours=1)).isoformat() + "Z",
                "end_time": (base_date + timedelta(hours=2, minutes=30)).isoformat() + "Z",
                "status": "COMPLETED",
                "parts_produced": 25
            },
            {
                "job_id": "JOB-005",
                "machine_id": "3DP001",
                "product_id": "Product-D1",
                "start_time": (base_date + timedelta(hours=3)).isoformat() + "Z",
                "end_time": (base_date + timedelta(hours=6)).isoformat() + "Z",
                "status": "COMPLETED",
                "parts_produced": 3
            }
        ]
        
        # Save job history
        with open(os.path.join(self.output_dir, "job_history.json"), "w") as f:
            json.dump({
                "date": "2025-07-17",
                "jobs": jobs,
                "summary": {
                    "total_jobs": len(jobs),
                    "failed_jobs": len([j for j in jobs if j["status"] == "FAILED"]),
                    "cooling_failures": len([j for j in jobs if j["status"] == "FAILED"])
                }
            }, f, indent=2)
        
        return jobs
    
    def _create_machine_shell(self, machine: Dict[str, Any]) -> AssetAdministrationShell:
        """Create AAS for a machine"""
        shell = AssetAdministrationShell(
            id=f"urn:aas:Machine:{machine['id']}",
            id_short=machine['id'],
            asset_information=AssetInformation(
                asset_kind=AssetKind.INSTANCE,
                global_asset_id=f"https://example.com/machines/{machine['serial']}",
                specific_asset_ids=[
                    {"name": "SerialNumber", "value": machine['serial']},
                    {"name": "ManufacturerID", "value": machine['manufacturer'].replace(" ", "_").upper()}
                ]
            ),
            administration=AdministrativeInformation(
                version="1",
                revision="0"
            )
        )
        
        # Add references to submodels - use machine ID instead of serial
        shell.submodels = [
            Reference(
                type="ModelReference",
                keys=[Key(type=KeyType.SUBMODEL, value=f"urn:aas:Nameplate:{machine['id']}")]
            ),
            Reference(
                type="ModelReference",
                keys=[Key(type=KeyType.SUBMODEL, value=f"urn:aas:TechnicalData:{machine['id']}")]
            ),
            Reference(
                type="ModelReference",
                keys=[Key(type=KeyType.SUBMODEL, value=f"urn:aas:OperationalData:{machine['id']}")]
            ),
            Reference(
                type="ModelReference",
                keys=[Key(type=KeyType.SUBMODEL, value=f"urn:aas:Documentation:{machine['id']}")]
            )
        ]
        
        return shell
    
    def _create_machine_submodels(self, machine: Dict[str, Any]) -> List:
        """Create submodels for a machine"""
        submodels = []
        
        # Nameplate
        nameplate = self.templates.create_nameplate_submodel(
            serial_number=machine['serial'],
            manufacturer_name=machine['manufacturer'],
            manufacturer_product_designation=machine['name'],
            manufacturer_article_number=machine['model'],
            year_of_construction="2024",
            hardware_version="1.0",
            software_version="3.2.1"
        )
        # Override ID to use machine ID instead of serial
        nameplate.id = f"urn:aas:Nameplate:{machine['id']}"
        submodels.append(nameplate)
        
        # Technical Data
        technical_data = self.templates.create_technical_data_submodel(
            serial_number=machine['serial'],
            power_consumption=machine['power_consumption'],
            weight=machine['weight'],
            dimensions=machine['dimensions'],
            operating_conditions=machine['operating_conditions'],
            requires_cooling_during_production=machine['cooling_required'],
            technical_specifications={
                "MachinePrecision": "±0.001mm",
                "MaxSpindleSpeed": "10000 RPM",
                "ToolCapacity": "40 tools"
            }
        )
        # Override ID to use machine ID instead of serial
        technical_data.id = f"urn:aas:TechnicalData:{machine['id']}"
        submodels.append(technical_data)
        
        # Operational Data
        # Generate static job history based on machine ID
        machine_jobs = []
        if machine['id'] == 'CNC002':
            machine_jobs = [
                {
                    "job_id": "JOB-001",
                    "product_id": "Product-B1",
                    "start_time": "2025-07-17T08:00:00Z",
                    "end_time": "2025-07-17T08:45:00Z",
                    "status": "FAILED",
                    "error_code": "cooling_system_error"
                },
                {
                    "job_id": "JOB-003",
                    "product_id": "Product-B1",
                    "start_time": "2025-07-17T12:00:00Z",
                    "end_time": "2025-07-17T12:15:00Z",
                    "status": "FAILED",
                    "error_code": "coolant_flow_insufficient"
                }
            ]
        elif machine['id'] == 'CNC001':
            machine_jobs = [
                {
                    "job_id": "JOB-002",
                    "product_id": "Product-C1",
                    "start_time": "2025-07-17T10:00:00Z",
                    "end_time": "2025-07-17T10:30:00Z",
                    "status": "FAILED",
                    "error_code": "temperature_exceeded"
                }
            ]
        elif machine['id'] == 'CNC003':
            machine_jobs = [
                {
                    "job_id": "JOB-004",
                    "product_id": "Product-A1",
                    "start_time": "2025-07-17T09:00:00Z",
                    "end_time": "2025-07-17T10:30:00Z",
                    "status": "COMPLETED"
                }
            ]
        elif machine['id'] == '3DP001':
            machine_jobs = [
                {
                    "job_id": "JOB-005",
                    "product_id": "Product-D1",
                    "start_time": "2025-07-17T11:00:00Z",
                    "end_time": "2025-07-17T14:00:00Z",
                    "status": "COMPLETED"
                }
            ]
        
        operational_data = self.templates.create_operational_data_submodel(
            serial_number=machine['serial'],
            machine_hours=machine['machine_hours'],
            production_cycles=machine['production_cycles'],
            last_maintenance_date=machine['last_maintenance'],
            error_count=5,
            current_status={
                "state": "IDLE",
                "utilization": 65.5,
                "current_job": None
            },
            job_history=machine_jobs
        )
        # Override ID to use machine ID instead of serial
        operational_data.id = f"urn:aas:OperationalData:{machine['id']}"
        submodels.append(operational_data)
        
        # Documentation
        documentation = self.templates.create_documentation_submodel(
            serial_number=machine['serial'],
            documents=[
                {
                    "type": "OperatingManual",
                    "title": f"{machine['name']} Operating Manual",
                    "version": "2.0",
                    "date": "2024-01-15T10:00:00Z",
                    "url": f"https://docs.example.com/{machine['serial']}/manual.pdf",
                    "format": "PDF",
                    "file_size": 15728640
                },
                {
                    "type": "MaintenanceManual",
                    "title": f"{machine['name']} Maintenance Guide",
                    "version": "1.5",
                    "date": "2024-02-01T14:00:00Z",
                    "url": f"https://docs.example.com/{machine['serial']}/maintenance.pdf",
                    "format": "PDF",
                    "file_size": 8388608
                }
            ]
        )
        # Override ID to use machine ID instead of serial
        documentation.id = f"urn:aas:Documentation:{machine['id']}"
        submodels.append(documentation)
        
        return submodels
    
    def _create_product_shell(self, product: Dict[str, Any]) -> AssetAdministrationShell:
        """Create AAS for a product"""
        shell = AssetAdministrationShell(
            id=f"urn:aas:Product:{product['id']}",
            id_short=product['id'],
            asset_information=AssetInformation(
                asset_kind=AssetKind.TYPE,  # Products are types, not instances
                global_asset_id=f"https://example.com/products/{product['id']}",
                specific_asset_ids=[
                    {"name": "ProductID", "value": product['id']},
                    {"name": "ProductType", "value": product['type']}
                ]
            ),
            administration=AdministrativeInformation(
                version="1",
                revision="0"
            )
        )
        
        # Add references to submodels
        shell.submodels = [
            Reference(
                type="ModelReference",
                keys=[Key(type=KeyType.SUBMODEL, value=f"urn:aas:ProductSpecification:{product['id']}")]
            ),
            Reference(
                type="ModelReference",
                keys=[Key(type=KeyType.SUBMODEL, value=f"urn:aas:ManufacturingRequirements:{product['id']}")]
            )
        ]
        
        return shell
    
    def _create_product_submodels(self, product: Dict[str, Any]) -> List:
        """Create submodels for a product"""
        from .aas_models import (
            Submodel, Property, SubmodelElementCollection,
            DataTypeDefXsd, ModelingKind, LangString
        )
        
        submodels = []
        
        # Product Specification
        spec_submodel = Submodel(
            id=f"urn:aas:ProductSpecification:{product['id']}",
            id_short="ProductSpecification",
            semantic_id=self.templates.create_reference("0173-1#01-AFZ651#001"),
            kind=ModelingKind.INSTANCE
        )
        
        # Material properties
        material_collection = SubmodelElementCollection(
            id_short="MaterialProperties",
            semantic_id=self.templates.create_reference("0173-1#01-AFZ652#001")
        )
        
        material_collection.value.extend([
            Property(
                id_short="Material",
                value_type=DataTypeDefXsd.STRING,
                value=product['material'],
                semantic_id=self.templates.create_reference("0173-1#02-AAO742#001")
            ),
            Property(
                id_short="Weight",
                value_type=DataTypeDefXsd.DECIMAL,
                value=product['weight'],
                semantic_id=self.templates.create_reference("0173-1#02-AAS627#002"),
                description=[LangString("en", "Weight in kg")]
            )
        ])
        
        # Dimensions
        if "dimensions" in product:
            dim = product["dimensions"]
            if "diameter" in dim:
                material_collection.value.append(
                    Property(
                        id_short="Diameter",
                        value_type=DataTypeDefXsd.DECIMAL,
                        value=dim["diameter"],
                        semantic_id=self.templates.create_reference("0173-1#02-AAO743#001"),
                        description=[LangString("en", "Diameter in mm")]
                    )
                )
            else:
                for key in ["length", "width", "height"]:
                    if key in dim:
                        material_collection.value.append(
                            Property(
                                id_short=key.capitalize(),
                                value_type=DataTypeDefXsd.DECIMAL,
                                value=dim[key],
                                description=[LangString("en", f"{key.capitalize()} in mm")]
                            )
                        )
        
        spec_submodel.submodel_elements.append(material_collection)
        
        # Quality requirements
        quality_collection = SubmodelElementCollection(
            id_short="QualityRequirements",
            semantic_id=self.templates.create_reference("0173-1#01-AFZ653#001")
        )
        
        quality_collection.value.append(
            Property(
                id_short="Tolerance",
                value_type=DataTypeDefXsd.DECIMAL,
                value=product['tolerance'],
                semantic_id=self.templates.create_reference("0173-1#02-AAO744#001"),
                description=[LangString("en", "Manufacturing tolerance in mm")]
            )
        )
        
        spec_submodel.submodel_elements.append(quality_collection)
        submodels.append(spec_submodel)
        
        # Manufacturing Requirements
        mfg_submodel = Submodel(
            id=f"urn:aas:ManufacturingRequirements:{product['id']}",
            id_short="ManufacturingRequirements",
            semantic_id=self.templates.create_reference("0173-1#01-AFZ654#001"),
            kind=ModelingKind.INSTANCE
        )
        
        # Process requirements
        process_collection = SubmodelElementCollection(
            id_short="ProcessRequirements",
            semantic_id=self.templates.create_reference("0173-1#01-AFZ655#001")
        )
        
        process_collection.value.extend([
            Property(
                id_short="requires_cooling_during_production",
                value_type=DataTypeDefXsd.BOOLEAN,
                value=str(product['requires_cooling']).lower(),
                semantic_id=self.templates.create_reference("0173-1#02-AAO745#001"),
                description=[LangString("en", "Requires cooling during production")]
            ),
            Property(
                id_short="StandardBatchSize",
                value_type=DataTypeDefXsd.INTEGER,
                value=product['batch_size'],
                semantic_id=self.templates.create_reference("0173-1#02-AAO746#001")
            )
        ])
        
        # Add material-specific requirements
        if "Aluminum" in product['material']:
            process_collection.value.append(
                Property(
                    id_short="CoolingMethod",
                    value_type=DataTypeDefXsd.STRING,
                    value="Flood cooling",
                    semantic_id=self.templates.create_reference("0173-1#02-AAO747#001")
                )
            )
        elif "Titanium" in product['material']:
            process_collection.value.append(
                Property(
                    id_short="CoolingMethod",
                    value_type=DataTypeDefXsd.STRING,
                    value="High-pressure cooling",
                    semantic_id=self.templates.create_reference("0173-1#02-AAO747#001")
                )
            )
        
        mfg_submodel.submodel_elements.append(process_collection)
        submodels.append(mfg_submodel)
        
        return submodels


if __name__ == "__main__":
    # Generate mock data when run directly
    generator = MockDataGenerator()
    generator.generate_all_data()