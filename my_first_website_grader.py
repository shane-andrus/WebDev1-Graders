# Import necessary libraries for extraction, fetching, and grading HTML
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def strip_trailing_slash(url):
    """Remove trailing slash from a URL for comparison."""
    return url.rstrip('/')

def grade_my_first_website(url, student_name, assignment_name):
    feedback = []
    total_score = 0  # Starting from zero, will add points based on rubric

    try:
        # Strip trailing slash from the submitted URL for comparison
        url_for_comparison = strip_trailing_slash(url)

        # Fetch the submitted page's HTML with SSL verification disabled
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')

        # Store pages to analyze: start with the submitted page
        pages = [(url, soup)]  # List of (url, soup) tuples
        base_url = urlparse(url).netloc  # Get the domain of the submitted URL
        internal_links = []

        # Find all internal links on the submitted page
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            parsed_href = urlparse(href)

            # Check if the link is internal (same domain or relative path)
            if not parsed_href.netloc or parsed_href.netloc == base_url:
                # Resolve relative URLs to absolute for fetching
                absolute_url = urljoin(url, href)
                # Avoid adding the same page (self-referential link)
                if strip_trailing_slash(absolute_url) != url_for_comparison:
                    internal_links.append((a_tag, absolute_url))

        # Fetch all linked pages to check for bi-directional linking
        linked_pages = []  # List of (url, soup, a_tag) tuples for linked pages
        for a_tag, linked_url in internal_links:
            try:
                linked_response = requests.get(linked_url, verify=False)
                linked_response.raise_for_status()
                linked_page_soup = BeautifulSoup(linked_response.text, 'html.parser')
                linked_pages.append((linked_url, linked_page_soup, a_tag))
                pages.append((linked_url, linked_page_soup))  # Add to pages for external link check
            except requests.exceptions.RequestException as e:
                feedback.append(f"Could not access linked page {linked_url}: {e}")

        # 1. Internal Links (13 points)
        internal_links_score = 0

        if internal_links and linked_pages:
            # Check if the submitted page has at least one valid internal link that opens in the same tab
            submitted_to_linked = False
            for linked_url, linked_soup, a_tag in linked_pages:
                # Check if the link opens in the same tab (no target="_blank")
                if a_tag.get('target') == '_blank':
                    feedback.append("Internal link on submitted page opens in a new tab, should open in the same tab.")
                    internal_links_score = 7
                    break
                submitted_to_linked = True
                break  # We only need one valid link to a linked page

            # Check if any linked page links back to the submitted page
            linked_to_submitted = False
            if submitted_to_linked:
                for linked_url, linked_soup, _ in linked_pages:
                    for a_tag in linked_soup.find_all('a', href=True):
                        href = a_tag['href']
                        parsed_href = urlparse(href)
                        if not parsed_href.netloc or parsed_href.netloc == base_url:
                            absolute_back_url = urljoin(linked_url, href)
                            # Strip trailing slashes for comparison
                            if strip_trailing_slash(absolute_back_url) == url_for_comparison:
                                # Check if the back link opens in the same tab
                                if a_tag.get('target') == '_blank':
                                    feedback.append("Internal link on linked page opens in a new tab, should open in the same tab.")
                                    internal_links_score = 7
                                    break
                                else:
                                    linked_to_submitted = True
                                    break
                    if linked_to_submitted:
                        break  # Found a page that links back, no need to check more

            # Award points based on bi-directional linking
            if submitted_to_linked and linked_to_submitted:
                internal_links_score = 13
                # No feedback since full points are awarded
            elif submitted_to_linked or linked_to_submitted:
                internal_links_score = 7
                if not linked_to_submitted:
                    feedback.append("Only one page links to the other or links have improper attributes.")
            else:
                internal_links_score = 0
                feedback.append("Internal links do not connect the pages correctly.")
        else:
            internal_links_score = 0
            feedback.append("Missing internal links to another page.")

        total_score += internal_links_score

        # 2. External Link (7 points)
        external_link_score = 0
        external_link_found = False

        # Check all pages for an external link
        for page_url, page_soup in pages:
            for a_tag in page_soup.find_all('a', href=True):
                href = a_tag['href']
                parsed_href = urlparse(href)

                # Check if the link is external (different domain and has a scheme like http/https)
                if parsed_href.netloc and parsed_href.netloc != base_url and parsed_href.scheme in ['http', 'https']:
                    external_link_found = True
                    # Check if it opens in a new tab
                    opens_in_new_tab = a_tag.get('target') == '_blank'

                    if opens_in_new_tab:
                        # Verify the link is an absolute path (already confirmed by urlparse having a scheme)
                        try:
                            # Optionally fetch the link to ensure it's accessible
                            external_response = requests.get(href, verify=False)
                            external_response.raise_for_status()
                            external_link_score = 7
                            # No feedback since full points are awarded
                        except requests.exceptions.RequestException:
                            external_link_score = 3
                            feedback.append(f"External link on {page_url} is not accessible, but uses an absolute path and opens in a new tab.")
                    else:
                        external_link_score = 3
                        feedback.append(f"External link on {page_url} uses an absolute path but does not open in a new tab.")
                    break  # Found an external link, no need to check more
            if external_link_found:
                break  # Stop checking other pages once an external link is found

        if not external_link_found:
            external_link_score = 0
            feedback.append("Missing an external link with an absolute path.")

        total_score += external_link_score

    except requests.exceptions.RequestException as e:
        feedback.append(f"Failed to fetch website: {e}")
        total_score = 0  # No score if the website can't be fetched

    # Ensure total score doesn't go below zero
    total_score = max(total_score, 0)

    # Return the score and feedback
    return total_score, feedback