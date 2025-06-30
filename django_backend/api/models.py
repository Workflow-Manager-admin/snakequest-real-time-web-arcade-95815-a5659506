from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid


class UserProfile(models.Model):
    """
    Extended user profile for Snake Game players.
    Stores additional information beyond Django's default User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.CharField(
        max_length=200, blank=True, null=True,
        help_text="URL or path to user avatar"
    )
    total_games_played = models.PositiveIntegerField(default=0)
    total_score = models.PositiveIntegerField(default=0)
    highest_score = models.PositiveIntegerField(default=0)
    level_reached = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    achievements = models.JSONField(
        default=list, blank=True, help_text="List of user achievements"
    )
    preferences = models.JSONField(
        default=dict, blank=True, help_text="User game preferences and settings"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_profiles'
        ordering = ['-highest_score', '-total_score']

    def __str__(self):
        return f"{self.user.username} - Profile"

    def update_stats(self, game_score, level):
        """Update user statistics after a game"""
        self.total_games_played += 1
        self.total_score += game_score
        if game_score > self.highest_score:
            self.highest_score = game_score
        if level > self.level_reached:
            self.level_reached = level
        self.save()


class GameSession(models.Model):
    """
    Represents a single Snake game session.
    Stores game state, progress, and metadata.
    """
    GAME_STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    score = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    duration = models.PositiveIntegerField(
        default=0, help_text="Game duration in seconds"
    )
    snake_length = models.PositiveIntegerField(default=1)
    food_consumed = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=GAME_STATUS_CHOICES, default='active')
    game_data = models.JSONField(
        default=dict, blank=True,
        help_text="Snake position, food position, obstacles, etc."
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'game_sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['player', '-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (f"{self.player.username} - Session {self.session_id.hex[:8]} - "
                f"Score: {self.score}")

    @property
    def is_active(self):
        return self.status == 'active'

    def end_game(self):
        """Mark the game session as completed"""
        from django.utils import timezone
        if self.status == 'active':
            self.status = 'completed'
            self.ended_at = timezone.now()
            self.save()
            # Update user profile stats
            if hasattr(self.player, 'profile'):
                self.player.profile.update_stats(self.score, self.level)


class Score(models.Model):
    """
    Individual score records for completed games.
    Provides detailed tracking of game performance.
    """
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores')
    game_session = models.OneToOneField(
        GameSession, on_delete=models.CASCADE, related_name='score_record'
    )
    points = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    level_achieved = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    time_played = models.PositiveIntegerField(
        help_text="Time played in seconds"
    )
    snake_length = models.PositiveIntegerField(default=1)
    food_eaten = models.PositiveIntegerField(default=0)
    obstacles_hit = models.PositiveIntegerField(default=0)
    bonus_points = models.PositiveIntegerField(default=0)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scores'
        ordering = ['-points', '-recorded_at']
        indexes = [
            models.Index(fields=['player', '-points']),
            models.Index(fields=['-points', '-recorded_at']),
        ]

    def __str__(self):
        return (f"{self.player.username} - {self.points} points - "
                f"Level {self.level_achieved}")

    @property
    def final_score(self):
        """Calculate final score with multiplier and bonus"""
        return int((self.points + self.bonus_points) * float(self.multiplier))


class Leaderboard(models.Model):
    """
    Leaderboard entries for different game categories.
    Maintains rankings and periodic leaderboard snapshots.
    """
    LEADERBOARD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
        ('level_based', 'Level Based'),
    ]

    leaderboard_type = models.CharField(max_length=20, choices=LEADERBOARD_TYPES)
    player = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='leaderboard_entries'
    )
    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name='leaderboard_entries'
    )
    rank = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    points = models.PositiveIntegerField()
    level = models.PositiveIntegerField(default=1)
    period_start = models.DateTimeField(
        help_text="Start of the leaderboard period"
    )
    period_end = models.DateTimeField(
        help_text="End of the leaderboard period"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(
        default=True, help_text="Is this the current active leaderboard"
    )

    class Meta:
        db_table = 'leaderboard'
        ordering = ['rank', '-points']
        unique_together = [
            ('leaderboard_type', 'player', 'period_start', 'period_end')
        ]
        indexes = [
            models.Index(fields=['leaderboard_type', 'is_current', 'rank']),
            models.Index(fields=['player', 'leaderboard_type']),
        ]

    def __str__(self):
        return (f"{self.leaderboard_type} - Rank {self.rank}: "
                f"{self.player.username} ({self.points} pts)")

    @classmethod
    def get_top_players(cls, leaderboard_type='all_time', limit=10):
        """Get top players for a specific leaderboard type"""
        return cls.objects.filter(
            leaderboard_type=leaderboard_type,
            is_current=True
        ).select_related('player', 'score')[:limit]


class Achievement(models.Model):
    """
    Game achievements that players can unlock.
    Defines different types of accomplishments in the game.
    """
    ACHIEVEMENT_TYPES = [
        ('score', 'Score Based'),
        ('level', 'Level Based'),
        ('time', 'Time Based'),
        ('special', 'Special Achievement'),
        ('streak', 'Streak Based'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    icon = models.CharField(
        max_length=200, blank=True, null=True, help_text="Icon URL or path"
    )
    criteria = models.JSONField(
        help_text="Achievement criteria in JSON format"
    )
    points_reward = models.PositiveIntegerField(
        default=0, help_text="Points awarded for this achievement"
    )
    is_hidden = models.BooleanField(
        default=False, help_text="Hidden until unlocked"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achievements'
        ordering = ['achievement_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.achievement_type})"


class PlayerAchievement(models.Model):
    """
    Junction table tracking which achievements players have unlocked.
    """
    player = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='player_achievements'
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, related_name='player_achievements'
    )
    unlocked_at = models.DateTimeField(auto_now_add=True)
    game_session = models.ForeignKey(
        GameSession, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = 'player_achievements'
        unique_together = [('player', 'achievement')]
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.player.username} - {self.achievement.name}"
