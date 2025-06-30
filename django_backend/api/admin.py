from django.contrib import admin
from .models import UserProfile, GameSession, Score, Leaderboard, Achievement, PlayerAchievement


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_games_played', 'highest_score', 'level_reached', 'is_active']
    list_filter = ['is_active', 'level_reached']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['player', 'score', 'level', 'status', 'started_at']
    list_filter = ['status', 'level', 'started_at']
    search_fields = ['player__username', 'session_id']
    readonly_fields = ['session_id', 'started_at', 'updated_at']


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ['player', 'points', 'level_achieved', 'time_played', 'recorded_at']
    list_filter = ['level_achieved', 'recorded_at']
    search_fields = ['player__username']
    readonly_fields = ['recorded_at']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['leaderboard_type', 'rank', 'player', 'points', 'is_current']
    list_filter = ['leaderboard_type', 'is_current', 'rank']
    search_fields = ['player__username']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'points_reward', 'is_active', 'is_hidden']
    list_filter = ['achievement_type', 'is_active', 'is_hidden']
    search_fields = ['name', 'description']


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ['player', 'achievement', 'unlocked_at']
    list_filter = ['achievement__achievement_type', 'unlocked_at']
    search_fields = ['player__username', 'achievement__name']
    readonly_fields = ['unlocked_at']
