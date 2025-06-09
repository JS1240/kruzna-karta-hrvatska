"""
Enhanced scraping pipeline with comprehensive data quality validation and duplicate detection.
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.data_quality import DataQualityService, get_data_quality_service
from ..models.schemas import EventCreate
from .entrio_scraper import EntrioScraper
from .croatia_scraper import CroatiaScraper


class EnhancedScrapingPipeline:
    """Advanced scraping pipeline with quality validation and duplicate detection."""
    
    def __init__(self, quality_threshold: float = 60.0, enable_duplicate_detection: bool = True):
        self.quality_threshold = quality_threshold
        self.enable_duplicate_detection = enable_duplicate_detection
        self.entrio_scraper = EntrioScraper()
        self.croatia_scraper = CroatiaScraper()
    
    async def scrape_all_sources(self, max_pages_per_source: int = 5) -> Dict[str, Any]:
        """Scrape events from all sources with enhanced quality processing."""
        print("=== Starting Enhanced Scraping Pipeline ===")
        start_time = datetime.now()
        
        pipeline_results = {
            "pipeline_start": start_time,
            "sources": {},
            "combined_results": {},
            "quality_report": {},
            "saved_events": 0,
            "total_processing_time": 0
        }
        
        # Scrape from all sources
        sources_config = [
            ("entrio.hr", self.entrio_scraper, max_pages_per_source),
            ("croatia.hr", self.croatia_scraper, max_pages_per_source)
        ]
        
        all_scraped_events = []
        
        for source_name, scraper, max_pages in sources_config:
            print(f"\n--- Scraping {source_name} ---")
            source_start = datetime.now()
            
            try:
                # Scrape events from source
                events = await scraper.scrape_events(max_pages=max_pages)
                
                source_end = datetime.now()
                source_duration = (source_end - source_start).total_seconds()
                
                pipeline_results["sources"][source_name] = {
                    "status": "success",
                    "events_scraped": len(events),
                    "scraping_duration": source_duration,
                    "events": events
                }
                
                all_scraped_events.extend(events)
                print(f"✓ {source_name}: {len(events)} events scraped in {source_duration:.2f}s")
                
            except Exception as e:
                source_end = datetime.now()
                source_duration = (source_end - source_start).total_seconds()
                
                pipeline_results["sources"][source_name] = {
                    "status": "error",
                    "error_message": str(e),
                    "events_scraped": 0,
                    "scraping_duration": source_duration,
                    "events": []
                }
                
                print(f"✗ {source_name}: Failed after {source_duration:.2f}s - {e}")
        
        print(f"\n--- Combined Scraping Results ---")
        print(f"Total events scraped: {len(all_scraped_events)}")
        
        # Process events with quality validation and duplicate detection
        if all_scraped_events:
            pipeline_results["combined_results"] = await self._process_events_with_quality_check(all_scraped_events)
        else:
            pipeline_results["combined_results"] = {
                "processing_summary": {
                    "original_count": 0,
                    "final_processable_count": 0
                }
            }
        
        # Calculate total processing time
        end_time = datetime.now()
        pipeline_results["total_processing_time"] = (end_time - start_time).total_seconds()
        pipeline_results["pipeline_end"] = end_time
        
        print(f"\n=== Pipeline Complete ===")
        print(f"Total processing time: {pipeline_results['total_processing_time']:.2f}s")
        print(f"Events saved: {pipeline_results['saved_events']}")
        
        return pipeline_results
    
    async def _process_events_with_quality_check(self, events: List[EventCreate]) -> Dict[str, Any]:
        """Process events with comprehensive quality validation."""
        print(f"\n--- Quality Processing Pipeline ---")
        processing_start = datetime.now()
        
        db = SessionLocal()
        try:
            # Initialize data quality service
            quality_service = DataQualityService(db)
            
            # Process events with quality validation and duplicate detection
            print("Running quality validation and duplicate detection...")
            processed_results = quality_service.process_scraped_events(
                events=events,
                quality_threshold=self.quality_threshold,
                remove_duplicates=self.enable_duplicate_detection
            )
            
            # Generate quality report
            quality_report = quality_service.generate_quality_report(processed_results)
            processed_results["quality_report"] = quality_report
            
            # Save valid events to database
            if processed_results["valid_events"]:
                print(f"Saving {len(processed_results['valid_events'])} valid events to database...")
                saved_count = quality_service.save_processed_events(processed_results)
                processed_results["saved_events"] = saved_count
            else:
                print("No valid events to save")
                processed_results["saved_events"] = 0
            
            processing_end = datetime.now()
            processing_duration = (processing_end - processing_start).total_seconds()
            processed_results["processing_duration"] = processing_duration
            
            # Print quality summary
            self._print_quality_summary(processed_results)
            
            return processed_results
            
        except Exception as e:
            print(f"Error in quality processing: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _print_quality_summary(self, processed_results: Dict[str, Any]):
        """Print comprehensive quality summary."""
        summary = processed_results["processing_summary"]
        report = processed_results.get("quality_report", {})
        
        print(f"\n--- Quality Processing Summary ---")
        print(f"📊 Original events: {summary['original_count']}")
        print(f"✅ Valid events: {summary['valid_count']}")
        print(f"⚠️  Low quality events: {summary['low_quality_count']}")
        print(f"❌ Invalid events: {summary['invalid_count']}")
        print(f"🔄 Batch duplicates removed: {summary['batch_duplicates_count']}")
        print(f"🔍 Database duplicates found: {summary['db_duplicates_count']}")
        print(f"💾 Final events saved: {summary['final_processable_count']}")
        
        if report:
            print(f"\n--- Quality Metrics ---")
            print(f"📈 Success rate: {report['success_rate']}%")
            print(f"⭐ Average quality score: {report['quality_metrics']['average_quality_score']}")
            print(f"🔁 Duplicate rate: {report['duplicate_analysis']['duplicate_rate']}%")
            
            # Print quality distribution
            dist = report['quality_metrics']['quality_distribution']
            print(f"🎯 Quality distribution: High({dist['high']}) Medium({dist['medium']}) Low({dist['low']})")
            
            # Print common issues
            if report['quality_metrics']['common_issues']:
                print(f"\n--- Most Common Issues ---")
                for i, (issue, count) in enumerate(report['quality_metrics']['common_issues'][:5], 1):
                    print(f"{i}. {issue} ({count} times)")
            
            # Print recommendations
            if report['recommendations']:
                print(f"\n--- Recommendations ---")
                for i, rec in enumerate(report['recommendations'], 1):
                    print(f"{i}. {rec}")
    
    async def scrape_single_source(self, source: str, max_pages: int = 5) -> Dict[str, Any]:
        """Scrape events from a single source with quality processing."""
        print(f"=== Scraping {source} with Enhanced Pipeline ===")
        start_time = datetime.now()
        
        # Select scraper
        if source.lower() == "entrio":
            scraper = self.entrio_scraper
        elif source.lower() == "croatia":
            scraper = self.croatia_scraper
        else:
            raise ValueError(f"Unknown source: {source}")
        
        # Scrape events
        try:
            events = await scraper.scrape_events(max_pages=max_pages)
            print(f"Scraped {len(events)} events from {source}")
            
            # Process with quality validation
            if events:
                processed_results = await self._process_events_with_quality_check(events)
            else:
                processed_results = {
                    "processing_summary": {
                        "original_count": 0,
                        "final_processable_count": 0
                    },
                    "saved_events": 0
                }
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            return {
                "source": source,
                "status": "success",
                "total_duration": total_duration,
                "scraping_results": processed_results,
                "events_saved": processed_results.get("saved_events", 0)
            }
            
        except Exception as e:
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            return {
                "source": source,
                "status": "error",
                "error_message": str(e),
                "total_duration": total_duration,
                "events_saved": 0
            }


class ScrapingMetricsCollector:
    """Collect and analyze scraping pipeline metrics."""
    
    @staticmethod
    def analyze_pipeline_performance(pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall pipeline performance."""
        analysis = {
            "performance_metrics": {},
            "source_comparison": {},
            "quality_analysis": {},
            "recommendations": []
        }
        
        # Performance metrics
        total_time = pipeline_results.get("total_processing_time", 0)
        total_events = 0
        total_saved = pipeline_results.get("saved_events", 0)
        
        # Source comparison
        source_metrics = {}
        for source_name, source_data in pipeline_results.get("sources", {}).items():
            events_count = source_data.get("events_scraped", 0)
            scraping_time = source_data.get("scraping_duration", 0)
            
            source_metrics[source_name] = {
                "events_scraped": events_count,
                "scraping_duration": scraping_time,
                "events_per_second": events_count / scraping_time if scraping_time > 0 else 0,
                "status": source_data.get("status", "unknown")
            }
            
            total_events += events_count
        
        analysis["source_comparison"] = source_metrics
        
        # Overall performance
        analysis["performance_metrics"] = {
            "total_events_scraped": total_events,
            "total_events_saved": total_saved,
            "total_processing_time": total_time,
            "overall_events_per_second": total_events / total_time if total_time > 0 else 0,
            "save_success_rate": (total_saved / total_events * 100) if total_events > 0 else 0
        }
        
        # Quality analysis from combined results
        combined_results = pipeline_results.get("combined_results", {})
        quality_report = combined_results.get("quality_report", {})
        
        if quality_report:
            analysis["quality_analysis"] = {
                "average_quality_score": quality_report.get("quality_metrics", {}).get("average_quality_score", 0),
                "success_rate": quality_report.get("success_rate", 0),
                "duplicate_rate": quality_report.get("duplicate_analysis", {}).get("duplicate_rate", 0),
                "quality_distribution": quality_report.get("quality_metrics", {}).get("quality_distribution", {}),
                "common_issues": quality_report.get("quality_metrics", {}).get("common_issues", [])
            }
        
        # Generate performance recommendations
        if analysis["performance_metrics"]["save_success_rate"] < 50:
            analysis["recommendations"].append("Low save success rate. Review data quality validation rules.")
        
        if analysis["performance_metrics"]["overall_events_per_second"] < 1:
            analysis["recommendations"].append("Low scraping performance. Consider optimizing scraper or using more parallel processing.")
        
        if any(source["status"] == "error" for source in source_metrics.values()):
            failed_sources = [name for name, data in source_metrics.items() if data["status"] == "error"]
            analysis["recommendations"].append(f"Failed sources detected: {', '.join(failed_sources)}. Check scraper configuration.")
        
        if quality_report and quality_report.get("duplicate_analysis", {}).get("duplicate_rate", 0) > 30:
            analysis["recommendations"].append("High duplicate rate. Consider adjusting scraping frequency or improving duplicate detection.")
        
        return analysis
    
    @staticmethod
    def generate_performance_report(pipeline_results: Dict[str, Any]) -> str:
        """Generate human-readable performance report."""
        analysis = ScrapingMetricsCollector.analyze_pipeline_performance(pipeline_results)
        
        report_lines = [
            "=== Enhanced Scraping Pipeline Performance Report ===",
            "",
            "📊 Overall Performance:",
            f"  • Total events scraped: {analysis['performance_metrics']['total_events_scraped']}",
            f"  • Total events saved: {analysis['performance_metrics']['total_events_saved']}",
            f"  • Processing time: {analysis['performance_metrics']['total_processing_time']:.2f}s",
            f"  • Scraping rate: {analysis['performance_metrics']['overall_events_per_second']:.2f} events/sec",
            f"  • Save success rate: {analysis['performance_metrics']['save_success_rate']:.1f}%",
            "",
        ]
        
        # Source comparison
        if analysis["source_comparison"]:
            report_lines.extend([
                "🌐 Source Performance:",
            ])
            for source, metrics in analysis["source_comparison"].items():
                status_emoji = "✅" if metrics["status"] == "success" else "❌"
                report_lines.append(
                    f"  {status_emoji} {source}: {metrics['events_scraped']} events in {metrics['scraping_duration']:.2f}s "
                    f"({metrics['events_per_second']:.2f} events/sec)"
                )
            report_lines.append("")
        
        # Quality analysis
        if analysis["quality_analysis"]:
            qa = analysis["quality_analysis"]
            report_lines.extend([
                "⭐ Quality Analysis:",
                f"  • Average quality score: {qa['average_quality_score']:.1f}/100",
                f"  • Success rate: {qa['success_rate']:.1f}%",
                f"  • Duplicate rate: {qa['duplicate_rate']:.1f}%",
            ])
            
            if qa["quality_distribution"]:
                dist = qa["quality_distribution"]
                report_lines.append(f"  • Quality distribution: High({dist.get('high', 0)}) Medium({dist.get('medium', 0)}) Low({dist.get('low', 0)})")
            
            if qa["common_issues"]:
                report_lines.extend([
                    "",
                    "⚠️  Common Issues:",
                ])
                for i, (issue, count) in enumerate(qa["common_issues"][:3], 1):
                    report_lines.append(f"  {i}. {issue} ({count} times)")
            
            report_lines.append("")
        
        # Recommendations
        if analysis["recommendations"]:
            report_lines.extend([
                "💡 Recommendations:",
            ])
            for i, rec in enumerate(analysis["recommendations"], 1):
                report_lines.append(f"  {i}. {rec}")
            report_lines.append("")
        
        report_lines.append("=== End of Report ===")
        
        return "\n".join(report_lines)


# Convenience functions for API endpoints
async def run_enhanced_scraping_pipeline(max_pages_per_source: int = 5, 
                                       quality_threshold: float = 60.0) -> Dict[str, Any]:
    """Run the enhanced scraping pipeline with all sources."""
    pipeline = EnhancedScrapingPipeline(
        quality_threshold=quality_threshold,
        enable_duplicate_detection=True
    )
    
    results = await pipeline.scrape_all_sources(max_pages_per_source=max_pages_per_source)
    
    # Generate performance analysis
    performance_analysis = ScrapingMetricsCollector.analyze_pipeline_performance(results)
    results["performance_analysis"] = performance_analysis
    
    # Generate readable report
    performance_report = ScrapingMetricsCollector.generate_performance_report(results)
    results["performance_report"] = performance_report
    
    return results


async def run_single_source_enhanced_scraping(source: str, max_pages: int = 5, 
                                            quality_threshold: float = 60.0) -> Dict[str, Any]:
    """Run enhanced scraping for a single source."""
    pipeline = EnhancedScrapingPipeline(
        quality_threshold=quality_threshold,
        enable_duplicate_detection=True
    )
    
    return await pipeline.scrape_single_source(source=source, max_pages=max_pages)