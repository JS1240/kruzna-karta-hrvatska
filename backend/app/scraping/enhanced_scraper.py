"""
Enhanced scraping pipeline with comprehensive data quality validation and duplicate detection.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List


logger = logging.getLogger(__name__)

from backend.app.core.data_quality import DataQualityService
from backend.app.core.database import SessionLocal
from backend.app.models.schemas import EventCreate
from app.scraping.croatia_scraper import CroatiaScraper
from app.scraping.entrio_scraper import EntrioScraper
from app.scraping.infozagreb_scraper import InfoZagrebScraper
from app.scraping.ulaznice_scraper import UlazniceScraper
from app.scraping.visitrijeka_scraper import VisitRijekaScraper
from app.scraping.vukovar_scraper import VukovarScraper
from app.scraping.visitsplit_scraper import VisitSplitScraper
from app.scraping.zadar_scraper import ZadarScraper
from app.scraping.tzdubrovnik_scraper import DubrovnikScraper
from app.scraping.visitvarazdin_scraper import VisitVarazdinScraper
from app.scraping.visitkarlovac_scraper import VisitKarlovacScraper
from app.scraping.visitopatija_scraper import VisitOpatijaScraper



class EnhancedScrapingPipeline:
    """Advanced scraping pipeline with quality validation and duplicate detection."""

    def __init__(
        self, quality_threshold: float = 60.0, enable_duplicate_detection: bool = True
    ):
        self.quality_threshold = quality_threshold
        self.enable_duplicate_detection = enable_duplicate_detection
        self.entrio_scraper = EntrioScraper()
        self.croatia_scraper = CroatiaScraper()
        self.infozagreb_scraper = InfoZagrebScraper()
        self.ulaznice_scraper = UlazniceScraper()
        self.visitrijeka_scraper = VisitRijekaScraper()
        self.vukovar_scraper = VukovarScraper()
        self.visitsplit_scraper = VisitSplitScraper()
        self.zadar_scraper = ZadarScraper()
        self.dubrovnik_scraper = DubrovnikScraper()
        self.visitvarazdin_scraper = VisitVarazdinScraper()
        self.visitkarlovac_scraper = VisitKarlovacScraper()
        self.visitopatija_scraper = VisitOpatijaScraper()

    async def scrape_all_sources(self, max_pages_per_source: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> Dict[str, Any]:
        """Scrape events from all sources with enhanced quality processing and address extraction."""
        logger.info("=== Starting Enhanced Scraping Pipeline ===")
        logger.info(f"Configuration: Playwright={use_playwright}, Detail fetching={fetch_details}")
        start_time = datetime.now()

        pipeline_results = {
            "pipeline_start": start_time,
            "sources": {},
            "combined_results": {},
            "quality_report": {},
            "saved_events": 0,
            "total_processing_time": 0,
            "enhanced_features": {
                "playwright_enabled": use_playwright,
                "detail_fetching_enabled": fetch_details
            }
        }

        # Scrape from all sources with enhanced configuration
        sources_config = [
            ("entrio.hr", self.entrio_scraper, max_pages_per_source),
            ("croatia.hr", self.croatia_scraper, max_pages_per_source),
            ("infozagreb.hr", self.infozagreb_scraper, max_pages_per_source),
            ("ulaznice.hr", self.ulaznice_scraper, max_pages_per_source),
            ("visitrijeka.hr", self.visitrijeka_scraper, max_pages_per_source),
            ("turizamvukovar.hr", self.vukovar_scraper, max_pages_per_source),
            ("visitsplit.com", self.visitsplit_scraper, max_pages_per_source),
            ("zadar.travel", self.zadar_scraper, max_pages_per_source),
            ("tzdubrovnik.hr", self.dubrovnik_scraper, max_pages_per_source),
            ("visitvarazdin.hr", self.visitvarazdin_scraper, max_pages_per_source),
            ("visitkarlovac.hr", self.visitkarlovac_scraper, max_pages_per_source),
            ("visitopatija.com", self.visitopatija_scraper, max_pages_per_source),
        ]
        all_scraped_events = []

        for source_name, scraper, max_pages in sources_config:
            logger.info(f"\n--- Scraping {source_name} ---")
            source_start = datetime.now()

            try:
                # Check if scraper supports enhanced features
                scraper_method = getattr(scraper, 'scrape_events', None)
                if scraper_method:
                    import inspect
                    sig = inspect.signature(scraper_method)
                    
                    # Enhanced scrapers (Ulaznice, VisitRijeka, VisitSplit, VisitOpatija, VisitVarazdin, Vukovar, Zadar, InfoZagreb) support additional parameters
                    if source_name in ["ulaznice.hr", "visitrijeka.hr", "visitsplit.com", "visitopatija.com", "visitvarazdin.hr", "turizamvukovar.hr", "zadar.travel", "infozagreb.hr"]:
                        # Use enhanced parameters for enhanced scrapers
                        events = await scraper.scrape_events(
                            max_pages=max_pages,
                            use_playwright=use_playwright,
                            fetch_details=fetch_details
                        )
                        logger.info(f"Using enhanced scraping for {source_name}")
                    else:
                        # Use standard parameters for other scrapers
                        events = await scraper.scrape_events(max_pages=max_pages)
                        logger.info(f"Using standard scraping for {source_name}")
                else:
                    # Fallback for scrapers without scrape_events method
                    events = []

                source_end = datetime.now()
                source_duration = (source_end - source_start).total_seconds()

                pipeline_results["sources"][source_name] = {
                    "status": "success",
                    "events_scraped": len(events),
                    "scraping_duration": source_duration,
                    "events": events,
                    "enhanced_features_used": source_name in ["ulaznice.hr", "visitrijeka.hr", "visitsplit.com", "visitopatija.com", "visitvarazdin.hr", "turizamvukovar.hr", "zadar.travel", "infozagreb.hr"]
                }

                all_scraped_events.extend(events)
                enhancement_note = " (enhanced)" if source_name in ["ulaznice.hr", "visitrijeka.hr", "visitsplit.com", "visitopatija.com", "visitvarazdin.hr", "turizamvukovar.hr", "zadar.travel", "infozagreb.hr"] else ""
                logger.info(
                    f"✓ {source_name}: {len(events)} events scraped in {source_duration:.2f}s{enhancement_note}"
                )

            except Exception as e:
                source_end = datetime.now()
                source_duration = (source_end - source_start).total_seconds()

                pipeline_results["sources"][source_name] = {
                    "status": "error",
                    "error_message": str(e),
                    "events_scraped": 0,
                    "scraping_duration": source_duration,
                    "events": [],
                    "enhanced_features_used": False
                }

                logger.error(f"✗ {source_name}: Failed after {source_duration:.2f}s - {e}")

        logger.info("\n--- Combined Scraping Results ---")
        logger.info(f"Total events scraped: {len(all_scraped_events)}")
        enhanced_count = sum(1 for source_data in pipeline_results["sources"].values() 
                           if source_data.get("enhanced_features_used", False))
        logger.info(f"Enhanced scrapers used: {enhanced_count}/12 (8 enhanced scrapers available: ulaznice.hr, visitrijeka.hr, visitsplit.com, visitopatija.com, visitvarazdin.hr, turizamvukovar.hr, zadar.travel, infozagreb.hr)")

        # Process events with quality validation and duplicate detection
        if all_scraped_events:
            pipeline_results["combined_results"] = (
                await self._process_events_with_quality_check(all_scraped_events)
            )
        else:
            pipeline_results["combined_results"] = {
                "processing_summary": {
                    "original_count": 0,
                    "final_processable_count": 0,
                }
            }

        # Calculate total processing time
        end_time = datetime.now()
        pipeline_results["total_processing_time"] = (
            end_time - start_time
        ).total_seconds()
        pipeline_results["pipeline_end"] = end_time

        logger.info("\n=== Pipeline Complete ===")
        logger.info(
            f"Total processing time: {pipeline_results['total_processing_time']:.2f}s"
        )
        logger.info(f"Events saved: {pipeline_results['saved_events']}")

        return pipeline_results

    async def _process_events_with_quality_check(
        self, events: List[EventCreate]
    ) -> Dict[str, Any]:
        """Process events with comprehensive quality validation."""
        logger.info("\n--- Quality Processing Pipeline ---")
        processing_start = datetime.now()

        db = SessionLocal()
        try:
            # Initialize data quality service
            quality_service = DataQualityService(db)

            # Process events with quality validation and duplicate detection
            logger.info("Running quality validation and duplicate detection...")
            processed_results = quality_service.process_scraped_events(
                events=events,
                quality_threshold=self.quality_threshold,
                remove_duplicates=self.enable_duplicate_detection,
            )

            # Generate quality report
            quality_report = quality_service.generate_quality_report(processed_results)
            processed_results["quality_report"] = quality_report

            # Save valid events to database
            if processed_results["valid_events"]:
                logger.info(
                    f"Saving {len(processed_results['valid_events'])} valid events to database..."
                )
                saved_count = quality_service.save_processed_events(processed_results)
                processed_results["saved_events"] = saved_count
            else:
                logger.info("No valid events to save")
                processed_results["saved_events"] = 0

            processing_end = datetime.now()
            processing_duration = (processing_end - processing_start).total_seconds()
            processed_results["processing_duration"] = processing_duration

            # Print quality summary
            self._print_quality_summary(processed_results)

            return processed_results

        except Exception as e:
            logger.error(f"Error in quality processing: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def _print_quality_summary(self, processed_results: Dict[str, Any]):
        """Print comprehensive quality summary."""
        summary = processed_results["processing_summary"]
        report = processed_results.get("quality_report", {})

        logger.info("\n--- Quality Processing Summary ---")
        logger.info(f"📊 Original events: {summary['original_count']}")
        logger.info(f"✅ Valid events: {summary['valid_count']}")
        logger.info(f"⚠️  Low quality events: {summary['low_quality_count']}")
        logger.info(f"❌ Invalid events: {summary['invalid_count']}")
        logger.info(f"🔄 Batch duplicates removed: {summary['batch_duplicates_count']}")
        logger.info(f"🔍 Database duplicates found: {summary['db_duplicates_count']}")
        logger.info(f"💾 Final events saved: {summary['final_processable_count']}")

        if report:
            logger.info("\n--- Quality Metrics ---")
            logger.info(f"📈 Success rate: {report['success_rate']}%")
            logger.info(
                f"⭐ Average quality score: {report['quality_metrics']['average_quality_score']}"
            )
            logger.info(
                f"🔁 Duplicate rate: {report['duplicate_analysis']['duplicate_rate']}%"
            )

            # Print quality distribution
            dist = report["quality_metrics"]["quality_distribution"]
            logger.info(
                f"🎯 Quality distribution: High({dist['high']}) Medium({dist['medium']}) Low({dist['low']})"
            )

            # Print common issues
            if report["quality_metrics"]["common_issues"]:
                logger.info("\n--- Most Common Issues ---")
                for i, (issue, count) in enumerate(
                    report["quality_metrics"]["common_issues"][:5], 1
                ):
                    logger.info(f"{i}. {issue} ({count} times)")

            # Print recommendations
            if report["recommendations"]:
                logger.info("\n--- Recommendations ---")
                for i, rec in enumerate(report["recommendations"], 1):
                    logger.info(f"{i}. {rec}")

    async def scrape_single_source(
        self, source: str, max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False
    ) -> Dict[str, Any]:
        """Scrape events from a single source with quality processing and enhanced address extraction."""
        logger.info(f"=== Scraping {source} with Enhanced Pipeline ===")
        logger.info(f"Configuration: Playwright={use_playwright}, Detail fetching={fetch_details}")
        start_time = datetime.now()

        # Select scraper
        if source.lower() == "entrio":
            scraper = self.entrio_scraper
        elif source.lower() == "croatia":
            scraper = self.croatia_scraper
        elif source.lower() == "infozagreb":
            scraper = self.infozagreb_scraper
        elif source.lower() == "ulaznice":
            scraper = self.ulaznice_scraper
        elif source.lower() == "visitrijeka":
            scraper = self.visitrijeka_scraper
        elif source.lower() == "vukovar":
            scraper = self.vukovar_scraper
        elif source.lower() == "visitsplit":
            scraper = self.visitsplit_scraper
        elif source.lower() == "zadar":
            scraper = self.zadar_scraper
        elif source.lower() == "tzdubrovnik":
            scraper = self.dubrovnik_scraper
        elif source.lower() == "visitvarazdin":
            scraper = self.visitvarazdin_scraper
        elif source.lower() == "visitkarlovac":
            scraper = self.visitkarlovac_scraper
        elif source.lower() == "visitopatija":
            scraper = self.visitopatija_scraper
        else:
            raise ValueError(f"Unknown source: {source}")

        # Scrape events with enhanced features if supported
        try:
            source_mapping = {
                "entrio": "entrio.hr",
                "croatia": "croatia.hr", 
                "infozagreb": "infozagreb.hr",
                "ulaznice": "ulaznice.hr",
                "visitrijeka": "visitrijeka.hr",
                "vukovar": "turizamvukovar.hr",
                "visitsplit": "visitsplit.com",
                "zadar": "zadar.travel",
                "tzdubrovnik": "tzdubrovnik.hr",
                "visitvarazdin": "visitvarazdin.hr",
                "visitkarlovac": "visitkarlovac.hr",
                "visitopatija": "visitopatija.com"
            }
            
            source_name = source_mapping.get(source.lower(), source)
            
            # Enhanced scrapers support additional parameters
            if source_name in ["ulaznice.hr", "visitrijeka.hr", "visitsplit.com", "visitopatija.com", "visitvarazdin.hr", "turizamvukovar.hr", "zadar.travel", "infozagreb.hr"]:
                events = await scraper.scrape_events(
                    max_pages=max_pages,
                    use_playwright=use_playwright,
                    fetch_details=fetch_details
                )
                logger.info(f"Used enhanced scraping for {source} (Playwright={use_playwright}, Details={fetch_details})")
                enhanced_features_used = True
            else:
                events = await scraper.scrape_events(max_pages=max_pages)
                logger.info(f"Used standard scraping for {source}")
                enhanced_features_used = False
                
            logger.info(f"Scraped {len(events)} events from {source}")

            # Process with quality validation
            if events:
                processed_results = await self._process_events_with_quality_check(
                    events
                )
            else:
                processed_results = {
                    "processing_summary": {
                        "original_count": 0,
                        "final_processable_count": 0,
                    },
                    "saved_events": 0,
                }

            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            return {
                "source": source,
                "status": "success",
                "total_duration": total_duration,
                "scraping_results": processed_results,
                "events_saved": processed_results.get("saved_events", 0),
                "enhanced_features_used": enhanced_features_used,
                "enhanced_features": {
                    "playwright_enabled": use_playwright if enhanced_features_used else False,
                    "detail_fetching_enabled": fetch_details if enhanced_features_used else False
                }
            }

        except Exception as e:
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            return {
                "source": source,
                "status": "error",
                "error_message": str(e),
                "total_duration": total_duration,
                "events_saved": 0,
                "enhanced_features_used": False
            }


class ScrapingMetricsCollector:
    """Collect and analyze scraping pipeline metrics."""

    @staticmethod
    def analyze_pipeline_performance(
        pipeline_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze overall pipeline performance."""
        analysis = {
            "performance_metrics": {},
            "source_comparison": {},
            "quality_analysis": {},
            "recommendations": [],
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
                "events_per_second": (
                    events_count / scraping_time if scraping_time > 0 else 0
                ),
                "status": source_data.get("status", "unknown"),
            }

            total_events += events_count

        analysis["source_comparison"] = source_metrics

        # Overall performance
        analysis["performance_metrics"] = {
            "total_events_scraped": total_events,
            "total_events_saved": total_saved,
            "total_processing_time": total_time,
            "overall_events_per_second": (
                total_events / total_time if total_time > 0 else 0
            ),
            "save_success_rate": (
                (total_saved / total_events * 100) if total_events > 0 else 0
            ),
        }

        # Quality analysis from combined results
        combined_results = pipeline_results.get("combined_results", {})
        quality_report = combined_results.get("quality_report", {})

        if quality_report:
            analysis["quality_analysis"] = {
                "average_quality_score": quality_report.get("quality_metrics", {}).get(
                    "average_quality_score", 0
                ),
                "success_rate": quality_report.get("success_rate", 0),
                "duplicate_rate": quality_report.get("duplicate_analysis", {}).get(
                    "duplicate_rate", 0
                ),
                "quality_distribution": quality_report.get("quality_metrics", {}).get(
                    "quality_distribution", {}
                ),
                "common_issues": quality_report.get("quality_metrics", {}).get(
                    "common_issues", []
                ),
            }

        # Generate performance recommendations
        if analysis["performance_metrics"]["save_success_rate"] < 50:
            analysis["recommendations"].append(
                "Low save success rate. Review data quality validation rules."
            )

        if analysis["performance_metrics"]["overall_events_per_second"] < 1:
            analysis["recommendations"].append(
                "Low scraping performance. Consider optimizing scraper or using more parallel processing."
            )

        if any(source["status"] == "error" for source in source_metrics.values()):
            failed_sources = [
                name
                for name, data in source_metrics.items()
                if data["status"] == "error"
            ]
            analysis["recommendations"].append(
                f"Failed sources detected: {', '.join(failed_sources)}. Check scraper configuration."
            )

        if (
            quality_report
            and quality_report.get("duplicate_analysis", {}).get("duplicate_rate", 0)
            > 30
        ):
            analysis["recommendations"].append(
                "High duplicate rate. Consider adjusting scraping frequency or improving duplicate detection."
            )

        return analysis

    @staticmethod
    def generate_performance_report(pipeline_results: Dict[str, Any]) -> str:
        """Generate human-readable performance report."""
        analysis = ScrapingMetricsCollector.analyze_pipeline_performance(
            pipeline_results
        )

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
            report_lines.extend(
                [
                    "🌐 Source Performance:",
                ]
            )
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
            report_lines.extend(
                [
                    "⭐ Quality Analysis:",
                    f"  • Average quality score: {qa['average_quality_score']:.1f}/100",
                    f"  • Success rate: {qa['success_rate']:.1f}%",
                    f"  • Duplicate rate: {qa['duplicate_rate']:.1f}%",
                ]
            )

            if qa["quality_distribution"]:
                dist = qa["quality_distribution"]
                report_lines.append(
                    f"  • Quality distribution: High({dist.get('high', 0)}) Medium({dist.get('medium', 0)}) Low({dist.get('low', 0)})"
                )

            if qa["common_issues"]:
                report_lines.extend(
                    [
                        "",
                        "⚠️  Common Issues:",
                    ]
                )
                for i, (issue, count) in enumerate(qa["common_issues"][:3], 1):
                    report_lines.append(f"  {i}. {issue} ({count} times)")

            report_lines.append("")

        # Recommendations
        if analysis["recommendations"]:
            report_lines.extend(
                [
                    "💡 Recommendations:",
                ]
            )
            for i, rec in enumerate(analysis["recommendations"], 1):
                report_lines.append(f"  {i}. {rec}")
            report_lines.append("")

        report_lines.append("=== End of Report ===")

        return "\n".join(report_lines)


# Convenience functions for API endpoints
async def run_enhanced_scraping_pipeline(
    max_pages_per_source: int = 5, quality_threshold: float = 60.0, 
    use_playwright: bool = True, fetch_details: bool = False
) -> Dict[str, Any]:
    """Run the enhanced scraping pipeline with all sources and optional address extraction."""
    pipeline = EnhancedScrapingPipeline(
        quality_threshold=quality_threshold, enable_duplicate_detection=True
    )

    results = await pipeline.scrape_all_sources(
        max_pages_per_source=max_pages_per_source,
        use_playwright=use_playwright,
        fetch_details=fetch_details
    )

    # Generate performance analysis
    performance_analysis = ScrapingMetricsCollector.analyze_pipeline_performance(
        results
    )
    results["performance_analysis"] = performance_analysis

    # Generate readable report
    performance_report = ScrapingMetricsCollector.generate_performance_report(results)
    results["performance_report"] = performance_report

    return results


async def run_single_source_enhanced_scraping(
    source: str, max_pages: int = 5, quality_threshold: float = 60.0,
    use_playwright: bool = True, fetch_details: bool = False
) -> Dict[str, Any]:
    """Run enhanced scraping for a single source with optional address extraction."""
    pipeline = EnhancedScrapingPipeline(
        quality_threshold=quality_threshold, enable_duplicate_detection=True
    )

    return await pipeline.scrape_single_source(
        source=source, max_pages=max_pages, 
        use_playwright=use_playwright, fetch_details=fetch_details
    )
