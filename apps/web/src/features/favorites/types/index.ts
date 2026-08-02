export interface FavoriteVideo {
  favorite_id: string;
  video_id: string;
  youtube_video_id: string;
  title: string;
  thumbnail_url: string | null;
  channel_title: string;
  favorited_at: string;
}
