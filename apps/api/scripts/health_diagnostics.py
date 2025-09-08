#!/usr/bin/env python3
"""
Health Diagnostics Script for StudioOps AI System

This script provides command-line access to system health information
and diagnostic capabilities for troubleshooting and monitoring.
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.health_monitoring_service import health_monitoring_service
from services.service_degradation_service import service_degradation_service, DegradationLevel
from services.startup_validation_service import startup_validation_service

class HealthDiagnostics:
    """Command-line health diagnostics tool"""
    
    def __init__(self):
        self.parser = self._setup_argument_parser()
    
    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """Setup command-line argument parser"""
        parser = argparse.ArgumentParser(
            description="StudioOps AI Health Diagnostics Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python health_diagnostics.py --check-all
  python health_diagnostics.py --service database
  python health_diagnostics.py --startup-validation
  python health_diagnostics.py --degradation-status
  python health_diagnostics.py --fix-bucket
            """
        )
        
        parser.add_argument(
            '--check-all',
            action='store_true',
            help='Run comprehensive health check for all services'
        )
        
        parser.add_argument(
            '--service',
            type=str,
            help='Check health of specific service (database, minio, trello_mcp, ai_service, observability)'
        )
        
        parser.add_argument(
            '--startup-validation',
            action='store_true',
            help='Run startup validation checks'
        )
        
        parser.add_argument(
            '--degradation-status',
            action='store_true',
            help='Show current service degradation status'
        )
        
        parser.add_argument(
            '--fix-bucket',
            action='store_true',
            help='Create missing MinIO bucket'
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        return parser
    
    async def run(self):
        """Run the diagnostics tool"""
        args = self.parser.parse_args()
        
        if not any([args.check_all, args.service, args.startup_validation, 
                   args.degradation_status, args.fix_bucket]):
            self.parser.print_help()
            return
        
        try:
            if args.check_all:
                await self._check_all_services(args.json, args.verbose)
            
            if args.service:
                await self._check_specific_service(args.service, args.json, args.verbose)
            
            if args.startup_validation:
                await self._run_startup_validation(args.json, args.verbose)
            
            if args.degradation_status:
                await self._show_degradation_status(args.json, args.verbose)
            
            if args.fix_bucket:
                await self._fix_minio_bucket(args.verbose)
                
        except Exception as e:
            if args.json:
                print(json.dumps({"error": str(e)}, indent=2))
            else:
                print(f"❌ Error: {e}")
            sys.exit(1)
    
    async def _check_all_services(self, json_output: bool, verbose: bool):
        """Check health of all services"""
        if not json_output:
            print("🏥 Running Comprehensive Health Check")
            print("=" * 50)
        
        health_status = await health_monitoring_service.get_system_health()
        
        if json_output:
            print(json.dumps(health_status, indent=2, default=str))
        else:
            self._print_health_status(health_status, verbose)
    
    async def _check_specific_service(self, service_name: str, json_output: bool, verbose: bool):
        """Check health of a specific service"""
        if not json_output:
            print(f"🔍 Checking {service_name} Service Health")
            print("=" * 50)
        
        health_status = await health_monitoring_service.get_system_health()
        
        if service_name not in health_status["services"]:
            if json_output:
                print(json.dumps({"error": f"Service '{service_name}' not found"}))
            else:
                print(f"❌ Service '{service_name}' not found")
                print(f"Available services: {', '.join(health_status['services'].keys())}")
            return
        
        service_health = health_status["services"][service_name]
        
        if json_output:
            print(json.dumps({
                "service": service_name,
                **service_health
            }, indent=2, default=str))
        else:
            self._print_service_health(service_name, service_health, verbose)
    
    async def _run_startup_validation(self, json_output: bool, verbose: bool):
        """Run startup validation"""
        if not json_output:
            print("🚀 Running Startup Validation")
            print("=" * 50)
        
        validation_results = await startup_validation_service.validate_system_startup()
        
        if json_output:
            print(json.dumps(validation_results, indent=2, default=str))
        else:
            self._print_startup_validation(validation_results, verbose)
    
    async def _show_degradation_status(self, json_output: bool, verbose: bool):
        """Show service degradation status"""
        if not json_output:
            print("⚠️ Service Degradation Status")
            print("=" * 50)
        
        summary = service_degradation_service.get_degradation_summary()
        all_states = service_degradation_service.get_all_service_states()
        user_status = service_degradation_service.get_user_facing_status()
        
        if json_output:
            print(json.dumps({
                "summary": summary,
                "service_states": all_states,
                "user_status": user_status
            }, indent=2, default=str))
        else:
            self._print_degradation_status(summary, all_states, user_status, verbose)
    
    async def _fix_minio_bucket(self, verbose: bool):
        """Fix missing MinIO bucket"""
        print("🔧 Fixing MinIO Bucket Configuration")
        print("=" * 50)
        
        try:
            from minio import Minio
            
            client = Minio(
                endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', 'studioops'),
                secret_key=os.getenv('MINIO_SECRET_KEY', 'studioops123'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            )
            
            bucket_name = "studioops-documents"
            
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                print(f"✅ Created bucket '{bucket_name}'")
            else:
                print(f"ℹ️ Bucket '{bucket_name}' already exists")
            
            # List all buckets to confirm
            buckets = client.list_buckets()
            print(f"📁 Available buckets: {[bucket.name for bucket in buckets]}")
            
        except Exception as e:
            print(f"❌ Failed to fix MinIO bucket: {e}")
            raise
    
    def _print_health_status(self, health_status: Dict[str, Any], verbose: bool):
        """Print health status in human-readable format"""
        overall_status = health_status["overall_status"]
        
        # Overall status
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }.get(overall_status, "❓")
        
        print(f"{status_emoji} Overall Status: {overall_status.upper()}")
        print(f"⏱️ Check Duration: {health_status['response_time_ms']:.2f}ms")
        print(f"🕐 Timestamp: {health_status['timestamp']}")
        print()
        
        # System info
        system_info = health_status["system_info"]
        print("📊 System Information:")
        print(f"  Version: {system_info['version']}")
        print(f"  Environment: {system_info['environment']}")
        print(f"  Uptime: {system_info['uptime_seconds']} seconds")
        print()
        
        # Services
        print("🔧 Service Status:")
        for service_name, service_data in health_status["services"].items():
            self._print_service_health(service_name, service_data, verbose)
    
    def _print_service_health(self, service_name: str, service_data: Dict[str, Any], verbose: bool):
        """Print individual service health"""
        status = service_data["status"]
        message = service_data["message"]
        response_time = service_data.get("response_time_ms", 0)
        
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓"
        }.get(status, "❓")
        
        print(f"  {status_emoji} {service_name}: {status.upper()}")
        print(f"    Message: {message}")
        print(f"    Response Time: {response_time:.2f}ms")
        
        if verbose and "details" in service_data:
            details = service_data["details"]
            print(f"    Details: {json.dumps(details, indent=6)}")
        
        print()
    
    def _print_startup_validation(self, validation_results: Dict[str, Any], verbose: bool):
        """Print startup validation results"""
        startup_successful = validation_results["startup_successful"]
        duration = validation_results["validation_duration_seconds"]
        
        status_emoji = "✅" if startup_successful else "❌"
        print(f"{status_emoji} Startup Validation: {'PASSED' if startup_successful else 'FAILED'}")
        print(f"⏱️ Duration: {duration:.2f}s")
        print()
        
        # Errors
        if validation_results["errors"]:
            print("❌ Errors:")
            for error in validation_results["errors"]:
                print(f"  • {error}")
            print()
        
        # Warnings
        if validation_results["warnings"]:
            print("⚠️ Warnings:")
            for warning in validation_results["warnings"]:
                print(f"  • {warning}")
            print()
        
        if verbose:
            print("📋 Detailed Results:")
            for section, result in validation_results["validation_results"].items():
                status = result.get("status", "unknown")
                status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
                print(f"  {status_emoji} {section}: {status.upper()}")
    
    def _print_degradation_status(self, summary: Dict[str, Any], all_states: Dict[str, Any], 
                                user_status: Dict[str, Any], verbose: bool):
        """Print service degradation status"""
        overall_status = summary["overall_status"]
        
        status_emoji = {
            "normal": "✅",
            "degraded": "⚠️",
            "critical": "❌"
        }.get(overall_status, "❓")
        
        print(f"{status_emoji} Overall Degradation Status: {overall_status.upper()}")
        print(f"📊 Services: {summary['healthy_services']} healthy, {summary['degraded_services']} degraded, {summary['critical_services']} critical")
        print()
        
        # User-facing status
        print("👤 User-Facing Status:")
        print(f"  Status: {user_status['status']}")
        print(f"  Message: {user_status['message']}")
        
        if user_status["service_impacts"]:
            print("  Service Impacts:")
            for impact in user_status["service_impacts"]:
                print(f"    • {impact}")
        print()
        
        # Individual service states
        if all_states["services"] and verbose:
            print("🔧 Individual Service States:")
            for service_name, state in all_states["services"].items():
                level = state["level"]
                timestamp = state["timestamp"]
                print(f"  • {service_name}: {level.value} (since {timestamp})")

def main():
    """Main entry point"""
    diagnostics = HealthDiagnostics()
    asyncio.run(diagnostics.run())

if __name__ == "__main__":
    main()