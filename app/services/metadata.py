import requests

ANILIST_API_URL = "https://graphql.anilist.co"


def search_manga(title):
    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA) {
        id
        title {
          romaji
          english
          native
        }
        description
        coverImage {
          large
          medium
        }
        status
        chapters
        genres
        averageScore
        siteUrl
      }
    }
    """
    try:
        response = requests.post(
            ANILIST_API_URL,
            json={"query": query, "variables": {"search": title}},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("Media")
    except (requests.RequestException, ValueError):
        return None


def search_manga_list(title, per_page=10):
    query = """
    query ($search: String, $perPage: Int) {
      Page(perPage: $perPage) {
        media(search: $search, type: MANGA) {
          id
          title {
            romaji
            english
            native
          }
          coverImage {
            large
            medium
          }
          chapters
          status
        }
      }
    }
    """
    try:
        response = requests.post(
            ANILIST_API_URL,
            json={"query": query, "variables": {"search": title, "perPage": per_page}},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("Page", {}).get("media", [])
    except (requests.RequestException, ValueError):
        return []