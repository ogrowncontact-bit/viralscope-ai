export interface Search {
  id: string;
  query: string;
  created_at: string;
}

export interface Video {
  id: string;
  youtube_video_id: string;
  title: string;
  channel_title: string;
  thumbnail_url: string | null;
  view_count: number;
  like_count: number;
  comment_count: number;
  duration_seconds: number | null;
  published_at: string | null;
}

export interface SearchResult {
  search: Search;
  videos: Video[];
}
