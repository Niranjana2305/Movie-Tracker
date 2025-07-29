from tortoise import fields, models

class Movie(models.Model):
    id = fields.IntField(pk=True)
    tmdb_id = fields.IntField(unique=True)
    title = fields.CharField(max_length=255)
    release_date = fields.DateField(null=True)
    overview = fields.TextField(null=True)
    poster_path = fields.CharField(max_length=255, null=True)
    media_type = fields.CharField(max_length=10, default="movie")
    cast_data = fields.TextField(null=True)
    genre_ids = fields.TextField(null=True)
     def get_cast(self):
        if self.cast_data:
            return json.loads(self.cast_data)
        return []
    def get_genre_ids(self):
        if self.genre_ids:
            return json.loads(self.genre_ids)
        return []

class Watchlist(models.Model):
    id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField("models.Movie", related_name="watchlisted")
    

