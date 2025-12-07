"""
Fetch job listings from xAI's careers page via Greenhouse API.
xAI uses Greenhouse for their job board, which provides a public API.
"""

import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import html


class XAIJobFetcher:
    """Fetches job listings from xAI's Greenhouse job board."""
    
    def __init__(self, board_token: str = "xai"):
        """
        Initialize the job fetcher.
        
        Args:
            board_token: Greenhouse board token for xAI (default: "xai")
        """
        self.board_token = board_token
        self.base_api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}"
        self.jobs_url = f"{self.base_api_url}/jobs"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Fetch all job listings from xAI's Greenhouse board.
        
        Returns:
            List of job dictionaries with basic information
        """
        try:
            response = self.session.get(self.jobs_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('jobs', [])
            
            print(f"[OK] Fetched {len(jobs)} job listings from xAI")
            return jobs
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching jobs: {e}")
            return []
    
    def fetch_job_details(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific job.
        
        Args:
            job_id: The Greenhouse job ID
            
        Returns:
            Dictionary with detailed job information or None if error
        """
        job_url = f"{self.base_api_url}/jobs/{job_id}"
        
        try:
            response = self.session.get(job_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Error fetching details for job {job_id}: {e}")
            return None
    
    def parse_job(self, job: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
        """
        Parse a job dictionary into a structured format.
        
        Args:
            job: Raw job data from Greenhouse API
            include_details: Whether to fetch full job details
            
        Returns:
            Structured job dictionary
        """
        parsed = {
            'id': job.get('id'),
            'title': job.get('title'),
            'location': job.get('location', {}).get('name', 'Not specified'),
            'department': job.get('departments', [{}])[0].get('name', 'Not specified') if job.get('departments') else 'Not specified',
            'office': job.get('offices', [{}])[0].get('name', 'Not specified') if job.get('offices') else 'Not specified',
            'application_url': job.get('absolute_url'),
            'greenhouse_url': f"https://boards.greenhouse.io/{self.board_token}/jobs/{job.get('id')}",
            'updated_at': job.get('updated_at'),
            'internal_job_id': job.get('internal_job_id'),
        }
        
        # Fetch detailed information if requested
        if include_details and job.get('id'):
            details = self.fetch_job_details(job['id'])
            if details:
                # Decode HTML entities in description
                raw_description = details.get('content', '')
                parsed['description'] = html.unescape(raw_description) if raw_description else ''
                parsed['requisition_id'] = details.get('requisition_id')
                
                # Extract additional metadata
                metadata = details.get('metadata', [])
                for item in metadata:
                    if item.get('name') == 'Salary Range':
                        parsed['salary_range'] = item.get('value')
                    elif item.get('name') == 'Employment Type':
                        parsed['employment_type'] = item.get('value')
                
                # Small delay to be respectful to the API
                time.sleep(0.5)
        
        return parsed
    
    def fetch_jobs(self, include_details: bool = False, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch and parse all jobs from xAI.
        
        Args:
            include_details: Whether to fetch full job descriptions (slower)
            search_term: Optional search term to filter jobs (searches in title)
            
        Returns:
            List of parsed job dictionaries
        """
        print(f"[*] Fetching jobs from xAI (board: {self.board_token})...")
        jobs = self.fetch_all_jobs()
        
        if not jobs:
            return []
        
        parsed_jobs = []
        for i, job in enumerate(jobs, 1):
            # Filter by search term if provided
            if search_term:
                title = job.get('title', '').lower()
                if search_term.lower() not in title:
                    continue
            
            print(f"  Processing job {i}/{len(jobs)}: {job.get('title', 'Unknown')}")
            parsed = self.parse_job(job, include_details=include_details)
            parsed_jobs.append(parsed)
        
        return parsed_jobs
    
    def save_jobs_to_json(self, jobs: List[Dict[str, Any]], filename: str = "xai_jobs.json"):
        """
        Save jobs to a JSON file.
        
        Args:
            jobs: List of job dictionaries
            filename: Output filename
        """
        output = {
            'fetched_at': datetime.now().isoformat(),
            'total_jobs': len(jobs),
            'board_token': self.board_token,
            'jobs': jobs
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"[*] Saved {len(jobs)} jobs to {filename}")
    
    def print_jobs_summary(self, jobs: List[Dict[str, Any]]):
        """Print a formatted summary of all jobs."""
        if not jobs:
            print("No jobs found.")
            return
        
        print(f"\n{'='*80}")
        print(f"xAI Job Listings Summary ({len(jobs)} jobs)")
        print(f"{'='*80}\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Location: {job['location']}")
            print(f"   Department: {job['department']}")
            print(f"   Apply: {job['application_url']}")
            if job.get('salary_range'):
                print(f"   Salary: {job['salary_range']}")
            print()


def main():
    """Main entry point."""
    import sys
    
    # Parse command line arguments
    include_details = '--details' in sys.argv or '-d' in sys.argv
    search_term = None
    
    # Check for search term
    if '--search' in sys.argv:
        idx = sys.argv.index('--search')
        if idx + 1 < len(sys.argv):
            search_term = sys.argv[idx + 1]
    elif '-s' in sys.argv:
        idx = sys.argv.index('-s')
        if idx + 1 < len(sys.argv):
            search_term = sys.argv[idx + 1]
    
    # Initialize fetcher
    fetcher = XAIJobFetcher()
    
    # Fetch jobs
    jobs = fetcher.fetch_jobs(include_details=include_details, search_term=search_term)
    
    if not jobs:
        print("[ERROR] No jobs found or error occurred.")
        return
    
    # Print summary
    fetcher.print_jobs_summary(jobs)
    
    # Save to JSON
    output_file = "xai_jobs.json"
    fetcher.save_jobs_to_json(jobs, output_file)
    
    print(f"\n[SUCCESS] Successfully fetched {len(jobs)} job(s)")
    print(f"[*] Full data saved to {output_file}")


if __name__ == "__main__":
    main()

