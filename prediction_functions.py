import pandas as pd
import numpy as np
import xgboost as xgb
import os
import pickle
def get_player_stats(player_name, court_type=None):
    """
    Получает актуальную статистику игрока из файла player_stats.csv,
    учитывая результат последнего матча.

    Параметры:
    ----------
    player_name : str
        Имя игрока
    court_type : str, optional
        Тип корта (если нужна статистика для конкретного покрытия)

    Возвращает:
    -----------
    dict
        Словарь с актуальной статистикой игрока
    """
    import pandas as pd

    try:
        # Загружаем файл статистики игроков
        df_stats = pd.read_csv('player_stats.csv')

        # Преобразуем даты в формат datetime
        df_stats['date'] = pd.to_datetime(df_stats['date'])

        # Фильтруем строки для указанного игрока
        player_stats = df_stats[df_stats['player'] == player_name]

        # Если игрок существует в статистике
        if not player_stats.empty:
            # Сортируем по дате и получаем самую свежую строку
            latest_stats = player_stats.sort_values('date').iloc[-1].to_dict()
            latest_result = latest_stats['result']

            # Обновляем cumulative_wins/losses с учетом последнего результата
            latest_stats['cumulative_wins'] += latest_result
            latest_stats['cumulative_losses'] += (1 - latest_result)

            # Обновляем streak
            if latest_result == 1:  # Победа
                latest_stats['streak'] = 1 if latest_stats['streak'] < 0 else latest_stats['streak'] + 1
            else:  # Поражение
                latest_stats['streak'] = -1 if latest_stats['streak'] > 0 else latest_stats['streak'] - 1

            # Обновляем court_wins/losses для данного корта
            latest_court = latest_stats['court']
            if court_type is None or court_type == latest_court:
                latest_stats['court_wins'] += latest_result
                latest_stats['court_losses'] += (1 - latest_result)

            # Обновляем wins_last_5 (добавляем новый результат, возможно удаляем старый)
            last_5_matches = player_stats.sort_values('date').tail(5)
            if len(last_5_matches) == 5:
                # Если уже было 5 матчей, вычитаем самый старый результат
                oldest_result = last_5_matches.iloc[0]['result']
                latest_stats['wins_last_5'] = latest_stats['wins_last_5'] - oldest_result + latest_result
            else:
                # Если было меньше 5 матчей, просто добавляем новый результат
                latest_stats['wins_last_5'] += latest_result

            # Обновляем wins_last_30d и matches_last_30d
            latest_date = latest_stats['date']
            thirty_days_ago = pd.to_datetime(latest_date) - pd.Timedelta(days=30)
            matches_30d = player_stats[(player_stats['date'] >= thirty_days_ago) &
                                       (player_stats['date'] <= latest_date)]

            # Удаляем результаты, которые стали старше 30 дней, и добавляем новый
            latest_stats['matches_last_30d'] = len(matches_30d)
            latest_stats['wins_last_30d'] = matches_30d['result'].sum()

            # Пересчитываем производные показатели
            latest_stats['win_rt'] = (latest_stats['cumulative_wins'] / latest_stats['cumulative_losses']
                                      if latest_stats['cumulative_losses'] > 0 else
                                      (1 if latest_stats['cumulative_wins'] > 0 else 0))

            latest_stats['court_win_rt'] = (latest_stats['court_wins'] / latest_stats['court_losses']
                                            if latest_stats['court_losses'] > 0 else
                                            (1 if latest_stats['court_wins'] > 0 else 0))

            latest_stats['win_rt_last_30'] = (latest_stats['wins_last_30d'] / latest_stats['matches_last_30d']
                                              if latest_stats['matches_last_30d'] > 0 else 0)

            return latest_stats
        else:
            # Если игрок новый, возвращаем значения по умолчанию
            return {
                'player': player_name,
                'cumulative_wins': 0,
                'cumulative_losses': 0,
                'streak': 0,
                'court_wins': 0,
                'court_losses': 0,
                'wins_last_5': 0,
                'wins_last_30d': 0,
                'matches_last_30d': 0,
                'win_rt': 0,
                'court_win_rt': 0,
                'win_rt_last_30': 0
            }
    except FileNotFoundError:
        # Если файл player_stats.csv не существует, возвращаем значения по умолчанию
        return {
            'player': player_name,
            'cumulative_wins': 0,
            'cumulative_losses': 0,
            'streak': 0,
            'court_wins': 0,
            'court_losses': 0,
            'wins_last_5': 0,
            'wins_last_30d': 0,
            'matches_last_30d': 0,
            'win_rt': 0,
            'court_win_rt': 0,
            'win_rt_last_30': 0
        }

def predict_using_match_data(match_data, model_path='best_xgb_model.json', feature_info_path='feature_info.pkl'):
    """
    Делает предсказание для одного матча

    Параметры:
    match_data (dict): Словарь с данными матча
    model_path (str): Путь к сохраненной модели
    feature_info_path (str): Путь к информации о признаках

    Возвращает:
    dict: Результаты предсказания, включая вероятность победы и прогноз
    """
    # Проверяем наличие файлов
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Файл модели не найден: {model_path}")

    if not os.path.exists(feature_info_path):
        raise FileNotFoundError(f"Файл с информацией о признаках не найден: {feature_info_path}")

    # Загружаем информацию о признаках
    with open(feature_info_path, 'rb') as f:
        feature_info = pickle.load(f)

    feature_cols = feature_info['feature_cols']

    # Загружаем модель
    model = xgb.XGBClassifier()
    model.load_model(model_path)

    # Проверяем наличие всех необходимых признаков
    missing_features = [col for col in feature_cols if col not in match_data]
    if missing_features:
        raise ValueError(f"В данных отсутствуют следующие признаки: {missing_features}")

    # Создаем DataFrame из данных матча
    match_df = pd.DataFrame([match_data])

    # Выбираем только нужные признаки
    match_features = match_df[feature_cols]

    # Делаем предсказание
    win_probability = model.predict_proba(match_features)[0, 1]
    prediction = model.predict(match_features)[0]

    result = {
        'win_probability': win_probability,
        'prediction': bool(prediction),
        'prediction_label': f"Игрок 1 победит с вероятностью {2 * win_probability - 1}" if prediction == 1 else f"Игрок 1 победит с вероятностью {-2 * win_probability + 1}"
    }

    return result

def make_prediction(name1, name2, r1=None, r2=None, court=None):
    r1_was_missing = 0
    r2_was_missing = 0

    if not r1:
        r1 = 329
        r1_was_missing = 1
    if not r2:
        r2 = 329
        r2_was_missing = 1

    result1 = get_player_stats(name1, court)
    result2 = get_player_stats(name2, court)

    match_data = {
        'Unnamed: 0': 20000,
        'r1': r1,
        'r2': r2,
        'r1_was_missing': r1_was_missing,
        'r2_was_missing': r2_was_missing,
        'rating_diff': r1 - r2,
        'rating_mean': (r1 + r2) / 2,
        'rating_ratio': r1 / r2,
        'p1_cumulative_wins': 2500,  # result1['cumulative_wins'],
        'p2_cumulative_wins': 500,  # result2['cumulative_wins'],
        'p1_cumulative_losses': result1['cumulative_losses'],
        'p2_cumulative_losses': result2['cumulative_losses'],
        'p1_streak': result1['streak'],
        'p2_streak': result2['streak'],
        'p1_court_wins': result1['court_wins'],
        'p2_court_wins': result2['court_wins'],
        'p1_court_losses': result1['court_losses'],
        'p2_court_losses': result2['court_losses'],
        'p1_wins_last_5': result1['wins_last_5'],
        'p2_wins_last_5': result2['wins_last_5'],
        'p1_wins_last_30d': result1['wins_last_30d'],
        'p2_wins_last_30d': result2['wins_last_30d'],
        'p1_matches_last_30d': result1['matches_last_30d'],
        'p2_matches_last_30d': result2['matches_last_30d'],
        'p1_win_rt': result1['win_rt'],
        'p2_win_rt': result2['win_rt'],
        'p1_court_win_rt': result1['court_win_rt'],
        'p2_court_win_rt': result2['court_win_rt'],
        'p1_win_rt_last_30': result1['win_rt_last_30'],
        'p2_win_rt_last_30': result2['win_rt_last_30'],
        'wins_diff': 2000,  # result1['cumulative_wins']-result2['cumulative_wins'],
        'losses_diff': result1['cumulative_losses'] - result2['cumulative_losses'],
        'streak_diff': result1['streak'] - result2['streak'],
        'court_wins_diff': result1['court_wins'] - result2['court_wins'],
        'court_losses_diff': result1['court_losses'] - result2['court_losses'],
        'last_5wins_diff': result1['wins_last_5'] - result2['wins_last_5'],
        'last_30d_wins_diff': result1['wins_last_30d'] - result2['wins_last_30d'],
        'last_30d_games_diff': result1['matches_last_30d'] - result2['matches_last_30d'],
        'win_rt_diff': result1['win_rt'] - result2['win_rt'],
        'court_win_rt_diff': result1['court_win_rt'] - result2['court_win_rt'],
        'win_rt_last_30_diff': result1['win_rt_last_30'] - result2['win_rt_last_30']
    }

    prediction = predict_using_match_data(match_data)
    return prediction
