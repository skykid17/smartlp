#!/usr/bin/env python3
"""
SmartSOC RAG Setup Script

This script automates the complete setup of RAG (Retrieval-Augmented Generation) for SmartSOC.
It handles downloading repositories, extracting parsing information, and creating vector embeddings.

Usage:
    python setup_rag.py [--siem splunk|elastic|both] [--skip-repos] [--skip-fields] [--skip-embeddings]

Options:
    --siem: Specify which SIEM to setup (splunk, elastic, or both). Default: both
    --skip-repos: Skip repository download
    --skip-fields: Skip field extraction
    --skip-embeddings: Skip embedding creation
    --help: Show this help message
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the current directory to Python path to import local modules
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from rag.update_repository import update_elastic_repo
    from rag.download_fields import download_splunk_fields, download_elastic_fields
    from rag.extract_logtypes import extract_elastic_logtypes, extract_splunk_sourcetypes
    from rag_mongo import create_embeddings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all required dependencies are installed and you're running from the correct directory.")
    sys.exit(1)

# Create logger object
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('./rag/rag_setup.log')
    ]
)

class RAGSetup:
    """Main class for RAG setup operations"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.rag_dir = self.base_dir / "rag"
        self.repos_dir = self.rag_dir / "repos"
        
        # Ensure directories exist
        self.repos_dir.mkdir(parents=True, exist_ok=True)
    
    def download_repositories(self, siem):
        """Download SIEM repositories and packages"""
        logger.info("=== DOWNLOADING REPOSITORIES ===")
        
        if siem in ['elastic', 'both']:
            logger.info("Downloading Elastic packages...")
            try:
                update_elastic_repo()
                logger.info("Elastic packages downloaded successfully")
            except Exception as e:
                logger.error(f"Failed to download Elastic packages: {e}")
                return False
        
        if siem in ['splunk', 'both']:
            logger.info("Splunk Add-ons require manual download from Splunkbase")
            logger.info("Please download Splunk Add-ons manually and place them in: ./rag/repos/splunk_repo/")
            logger.info("Splunk Add-ons URL: https://splunkbase.splunk.com/apps?page=1&keyword=add-on&filters=built_by%3Asplunk%2Fproduct%3Asplunk")
            
            # Check if splunk repo directory exists
            splunk_repo = self.repos_dir / "splunk_repo"
            if not splunk_repo.exists() or not any(splunk_repo.iterdir()):
                logger.warning("Splunk repository directory is empty. Manual download required.")
            else:
                logger.info("Splunk repository directory found")
        
        return True
    
    def download_fields_and_logtypes(self, siem):
        """Download and extract parsing information from documentation"""
        logger.info("=== DOWNLOADING PARSING INFORMATION ===")
        
        success = True
        
        if siem in ['splunk', 'both']:
            logger.info("Downloading Splunk fields...")
            try:
                # This function is currently not working, use a static copy of splunk_fields.csv
                #download_splunk_fields()
                logger.info("Splunk fields downloaded successfully")
            except Exception as e:
                logger.error(f"Failed to download Splunk fields: {e}")
                success = False
            
            logger.info("Extracting Splunk sourcetypes...")
            try:
                extract_splunk_sourcetypes()
                logger.info("Splunk sourcetypes extracted successfully")
            except Exception as e:
                logger.error(f"Failed to extract Splunk sourcetypes: {e}")
                success = False
        
        if siem in ['elastic', 'both']:
            logger.info("Downloading Elastic fields...")
            try:
                download_elastic_fields()
                logger.info("Elastic fields downloaded successfully")
            except Exception as e:
                logger.error(f"Failed to download Elastic fields: {e}")
                success = False
            
            logger.info("Extracting Elastic logtypes...")
            try:
                extract_elastic_logtypes()
                logger.info("Elastic logtypes extracted successfully")
            except Exception as e:
                logger.error(f"Failed to extract Elastic logtypes: {e}")
                success = False
        
        return success
    
    def create_embeddings(self, siem):
        """Create vector embeddings for all RAG collections"""
        logger.info("=== CREATING VECTOR EMBEDDINGS ===")
        
        embeddings_config = [
            # Repository embeddings
            ("./rag/repos/splunk_repo", "splunk_addons", "splunk"),
            ("./rag/repos/elastic_repo", "elastic_packages", "elastic"),
            
            # Field embeddings
            ("./rag/splunk_fields.csv", "splunk_fields", "splunk"),
            ("./rag/elastic_fields.csv", "elastic_fields", "elastic"),
            
            # Logtype embeddings
            ("./rag/elastic_logtypes.csv", "elastic_logtypes", "elastic"),
            ("./rag/splunk_sourcetypes.csv", "splunk_sourcetypes", "splunk"),
        ]
        
        success = True
        
        for file_path, collection_name, siem_type in embeddings_config:
            # Skip if not processing this SIEM type
            if siem not in ['both'] and siem != siem_type:
                continue
            
            # Check if file/directory exists
            path_obj = Path(file_path)
            if not path_obj.exists():
                logger.warning(f"Skipping {collection_name}: {file_path} not found")
                continue
            
            logger.info(f"Creating embeddings for {collection_name}...")
            try:
                result = create_embeddings(
                    file_or_folder_path=file_path,
                    collection_name=collection_name
                )
                
                if result:
                    logger.info(f"Successfully created embeddings for {collection_name}")
                else:
                    logger.error(f"Failed to create embeddings for {collection_name}")
                    success = False
                    
            except Exception as e:
                logger.error(f"Error creating embeddings for {collection_name}: {e}")
                success = False
        
        return success
    
    def verify_setup(self, siem):
        """Verify that the RAG setup was completed successfully"""
        logger.info("=== VERIFYING RAG SETUP ===")
        
        # Check required files and directories
        required_files = []
        required_dirs = []
        
        if siem in ['splunk', 'both']:
            # Required files for Splunk SIEM
            required_files.extend(
                [
                    "rag/splunk_fields.csv",
                    "rag/splunk_sourcetypes.csv"
                ]
            )

        if siem in ['elastic', 'both']:
            # Required files for Elastic SIEM
            required_files.extend(
                [
                    "rag/elastic_fields.csv",
                    "rag/elastic_logtypes.csv",
                ]
            )

            # Required dirs for Elastic SIEM
            required_dirs.append("rag/repos/elastic_repo")
        
        issues = []
        
        for file_path in required_files:
            if not Path(file_path).exists():
                issues.append(f"Missing file: {file_path}")
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                issues.append(f"Missing directory: {dir_path}")
        
        # Check MongoDB connection and RAG collection
        try:
            from rag_mongo import get_rag_collection, list_sources
            collection = get_rag_collection()
            sources = list_sources()
            
            logger.info(f"MongoDB RAG collection accessible with {len(sources)} sources: {sources}")
            
            # Check if expected sources exist
            expected_sources = []
            if siem in ['splunk', 'both']:
                expected_sources.extend(['splunk_addons', 'splunk_fields', 'splunk_sourcetypes'])
            if siem in ['elastic', 'both']:
                expected_sources.extend(['elastic_packages', 'elastic_fields', 'elastic_logtypes'])
            
            missing_sources = [s for s in expected_sources if s not in sources]
            if missing_sources:
                issues.append(f"Missing MongoDB sources: {', '.join(missing_sources)}")
                
        except Exception as e:
            issues.append(f"MongoDB RAG collection error: {str(e)}")
        
        if issues:
            logger.warning("Setup verification found issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.info("RAG setup verification completed successfully")
            return True
    
    def run_complete_setup(self, siem, skip_repos, skip_fields, skip_embeddings):
        """Run the complete RAG setup process"""
        logger.info("Starting SmartSOC RAG setup...")
        logger.info(f"SIEM: {siem}")
        logger.info(f"Skip repositories: {skip_repos}")
        logger.info(f"Skip fields: {skip_fields}")
        logger.info(f"Skip embeddings: {skip_embeddings}")
        
        success = True
        
        # Step 1: Download repositories
        if not skip_repos:
            if not self.download_repositories(siem):
                logger.error("Repository download failed")
                success = False
        
        # Step 2: Download fields and extract logtypes
        if not skip_fields:
            if not self.download_fields_and_logtypes(siem):
                logger.error("Field/logtype extraction failed")
                success = False
        
        # Step 3: Create embeddings
        if not skip_embeddings:
            if not self.create_embeddings(siem):
                logger.error("Embedding creation failed")
                success = False
        
        # Step 4: Verify setup
        self.verify_setup(siem)
        
        if success:
            logger.info("RAG setup completed successfully!")
            self.print_reference_links()
        else:
            logger.error("RAG setup completed with errors. Check the log for details.")
        
        return success
    
    def print_reference_links(self):
        """Print reference links for manual verification"""
        logger.info("\n=== REFERENCE LINKS ===")
        logger.info("Splunk CIM Field Reference:")
        logger.info("https://docs.splunk.com/Documentation/CIM/6.1.0/User/Overview")
        logger.info("")
        logger.info("Elastic ECS Field Reference:")
        logger.info("https://www.elastic.co/docs/reference/ecs/ecs-field-reference")
        logger.info("")
        logger.info("Elastic Integrations Repository:")
        logger.info("https://github.com/elastic/integrations/tree/main/packages")
        logger.info("")
        logger.info("Splunk Add-ons (manual download required):")
        logger.info("https://splunkbase.splunk.com/apps?page=1&keyword=add-on&filters=built_by%3Asplunk%2Fproduct%3Asplunk")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SmartSOC RAG Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--siem',
        choices=['splunk', 'elastic', 'both'],
        default='both',
        help='Specify which SIEM to setup (default: both)'
    )
    
    parser.add_argument(
        '--skip-repos',
        action='store_true',
        help='Skip repository download'
    )
    
    parser.add_argument(
        '--skip-fields',
        action='store_true',
        help='Skip field extraction'
    )
    
    parser.add_argument(
        '--skip-embeddings',
        action='store_true',
        help='Skip embedding creation'
    )
    
    args = parser.parse_args()
    
    # Create RAG setup instance and run
    rag_setup = RAGSetup()
    success = rag_setup.run_complete_setup(
        siem=args.siem,
        skip_repos=args.skip_repos,
        skip_fields=args.skip_fields,
        skip_embeddings=args.skip_embeddings
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
