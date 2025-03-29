import pandas as pd
import numpy as np
import os



def add_batch_matches_and_update_stats(new_matches_xlsx):
    df = pd.read_excel(new_matches_xlsx)
    columns_to_keep = ['Игрок 1', 'Игрок 2', 'Дата', 'Круг', 'Корт', 'R1', 'R2', 'Сеты']
    df = df[columns_to_keep]
    df['Игрок 1'] = df['Игрок 1'].str.replace(r'^\([^)]*\)\s*', '', regex=True)
    df['Игрок 2'] = df['Игрок 2'].str.replace(r'^\([^)]*\)\s*', '', regex=True)
    df.columns = ['player1', 'player2', 'date', 'stage', 'court', 'r1', 'r2', 'sets']
    new_matches = df

    # Проверка необходимых колонок
    required_columns = ['player1', 'player2', 'date', 'r1', 'r2', 'sets', 'court', 'stage']

    matches = new_matches.copy()
    matches['date'] = pd.to_datetime(matches['date'])

    # Сортируем по дате - это критически важно для правильного обновления статистики
    matches = matches.sort_values('date').reset_index(drop=True)

    # Загружаем текущую статистику игроков, если она существует
    if os.path.exists('player_stats.csv'):
        player_stats_df = pd.read_csv('player_stats.csv')
        player_stats_df['date'] = pd.to_datetime(player_stats_df['date'])
    else:
        player_stats_df = pd.DataFrame(columns=[
            'player', 'court', 'stage', 'date', 'result', 'is_player1',
            'match_id', 'cumulative_wins', 'cumulative_losses', 'streak',
            'court_wins', 'court_losses', 'wins_last_5', 'wins_last_30d',
            'matches_last_30d', 'win_rt', 'court_win_rt', 'win_rt_last_30'
        ])

    # Словари для хранения актуальной статистики и последних 5 матчей для каждого игрока
    player_stats_cache = {}
    player_last_5_matches = {}

    # Список для новых записей статистики
    new_stats_rows = []

    print(f"Обработка {len(matches)} новых матчей...")

    # Генерируем match_id, начиная со следующего после максимального в текущей статистике
    max_match_id = player_stats_df['match_id'].max() if not player_stats_df.empty else -1
    current_match_id = max_match_id + 1

    # Обрабатываем каждый матч
    for idx, match in matches.iterrows():
        if idx % 100 == 0 and idx > 0:
            print(f"Обработано {idx} матчей...")

        # Анализируем результат матча
        if pd.isnull(match['sets']) or match['sets'] == '':
            continue  # Пропускаем матчи без результата

        try:
            sets_parts = match['sets'].split('-')
            sets1 = int(sets_parts[0])
            sets2 = int(sets_parts[1])
            player1_win = 1 if sets1 > sets2 else 0
        except:
            continue  # Пропускаем некорректные записи сетов

        match_date = match['date']
        court_type = match['court']

        # Обрабатываем статистику для player1
        p1_stats = get_player_stats(
            match['player1'],
            player_stats_cache,
            player_last_5_matches,
            player_stats_df,
            match_date,
            court_type
        )

        # Создаем запись статистики для player1
        p1_record = {
            'player': match['player1'],
            'court': court_type,
            'stage': match['stage'],
            'date': match_date,
            'result': player1_win,
            'is_player1': True,
            'match_id': current_match_id,
            'cumulative_wins': p1_stats['cumulative_wins'],
            'cumulative_losses': p1_stats['cumulative_losses'],
            'streak': p1_stats['streak'],
            'court_wins': p1_stats['court_wins'],
            'court_losses': p1_stats['court_losses'],
            'wins_last_5': p1_stats['wins_last_5'],
            'wins_last_30d': p1_stats['wins_last_30d'],
            'matches_last_30d': p1_stats['matches_last_30d'],
            'win_rt': p1_stats['win_rt'],
            'court_win_rt': p1_stats['court_win_rt'],
            'win_rt_last_30': p1_stats['win_rt_last_30']
        }
        new_stats_rows.append(p1_record)

        # Обрабатываем статистику для player2
        p2_stats = get_player_stats(
            match['player2'],
            player_stats_cache,
            player_last_5_matches,
            player_stats_df,
            match_date,
            court_type
        )

        # Создаем запись статистики для player2
        p2_record = {
            'player': match['player2'],
            'court': court_type,
            'stage': match['stage'],
            'date': match_date,
            'result': 1 - player1_win,
            'is_player1': False,
            'match_id': current_match_id,
            'cumulative_wins': p2_stats['cumulative_wins'],
            'cumulative_losses': p2_stats['cumulative_losses'],
            'streak': p2_stats['streak'],
            'court_wins': p2_stats['court_wins'],
            'court_losses': p2_stats['court_losses'],
            'wins_last_5': p2_stats['wins_last_5'],
            'wins_last_30d': p2_stats['wins_last_30d'],
            'matches_last_30d': p2_stats['matches_last_30d'],
            'win_rt': p2_stats['win_rt'],
            'court_win_rt': p2_stats['court_win_rt'],
            'win_rt_last_30': p2_stats['win_rt_last_30']
        }
        new_stats_rows.append(p2_record)

        # Обновляем кеш статистики обоих игроков
        update_player_cache(
            player_stats_cache,
            player_last_5_matches,
            match['player1'],
            player1_win,
            match_date,
            court_type
        )

        update_player_cache(
            player_stats_cache,
            player_last_5_matches,
            match['player2'],
            1 - player1_win,
            match_date,
            court_type
        )

        current_match_id += 1

    print("Объединение данных...")

    # Объединяем существующую статистику с новыми данными
    updated_stats = pd.concat([player_stats_df, pd.DataFrame(new_stats_rows)], ignore_index=True)

    print("Сохранение обновленной статистики...")
    updated_stats.to_csv('player_stats.csv', index=False)

    print(f"Готово! Добавлено {len(new_stats_rows)} записей статистики.")

    return updated_stats


def get_player_stats(player_name, player_stats_cache, player_last_5_matches, player_stats_df, match_date, court_type):
    """
    Получает актуальную статистику игрока на момент перед матчем
    """
    # Проверяем кеш
    if player_name in player_stats_cache:
        return player_stats_cache[player_name]

    # Фильтруем статистику игрока до текущей даты
    player_stats = player_stats_df[(player_stats_df['player'] == player_name) &
                                   (player_stats_df['date'] < match_date)]

    # Инициализируем историю последних 5 матчей
    if player_name not in player_last_5_matches:
        player_last_5_matches[player_name] = []

        # Если есть прошлая статистика, загружаем последние 5 матчей
        if not player_stats.empty:
            recent_matches = player_stats.sort_values('date').tail(5)
            for _, match in recent_matches.iterrows():
                player_last_5_matches[player_name].append({
                    'date': match['date'],
                    'result': match['result']
                })

    if not player_stats.empty:
        # Берем последнюю доступную статистику перед матчем
        latest_stats = player_stats.sort_values('date').iloc[-1].to_dict()

        # Обновляем статистику за 30 дней
        thirty_days_ago = match_date - pd.Timedelta(days=30)
        matches_30d = player_stats[(player_stats['date'] >= thirty_days_ago) &
                                   (player_stats['date'] < match_date)]

        latest_stats['matches_last_30d'] = len(matches_30d)
        latest_stats['wins_last_30d'] = matches_30d['result'].sum()

        # Добавляем последний результат к накопительным показателям
        last_result = latest_stats['result']
        latest_stats['cumulative_wins'] += last_result
        latest_stats['cumulative_losses'] += (1 - last_result)

        # Обновляем streak
        if last_result == 1:  # Победа
            latest_stats['streak'] = 1 if latest_stats['streak'] < 0 else latest_stats['streak'] + 1
        else:  # Поражение
            latest_stats['streak'] = -1 if latest_stats['streak'] > 0 else latest_stats['streak'] - 1

        # Обновляем статистику по корту
        if court_type == latest_stats['court']:
            latest_stats['court_wins'] += last_result
            latest_stats['court_losses'] += (1 - last_result)
        else:
            # Ищем статистику для указанного корта
            court_stats = player_stats[player_stats['court'] == court_type]
            if not court_stats.empty:
                latest_court = court_stats.sort_values('date').iloc[-1]
                latest_stats['court_wins'] = latest_court['court_wins'] + latest_court['result']
                latest_stats['court_losses'] = latest_court['court_losses'] + (1 - latest_court['result'])
            else:
                # Если для этого корта еще нет статистики
                latest_stats['court_wins'] = 0
                latest_stats['court_losses'] = 0

        # Пересчитываем производные показатели
        if latest_stats['cumulative_losses'] > 0:
            latest_stats['win_rt'] = latest_stats['cumulative_wins'] / latest_stats['cumulative_losses']
        else:
            latest_stats['win_rt'] = 1.0 if latest_stats['cumulative_wins'] > 0 else 0.0

        if latest_stats['court_losses'] > 0:
            latest_stats['court_win_rt'] = latest_stats['court_wins'] / latest_stats['court_losses']
        else:
            latest_stats['court_win_rt'] = 1.0 if latest_stats['court_wins'] > 0 else 0.0

        if latest_stats['matches_last_30d'] > 0:
            latest_stats['win_rt_last_30'] = latest_stats['wins_last_30d'] / latest_stats['matches_last_30d']
        else:
            latest_stats['win_rt_last_30'] = 0.0

        player_stats_cache[player_name] = latest_stats
        return latest_stats
    else:
        # Для нового игрока создаем записи по умолчанию
        default_stats = {
            'player': player_name,
            'court': court_type,
            'stage': '',
            'date': match_date,
            'result': 0,  # Будет заполнено позже
            'is_player1': True,  # Будет заполнено позже
            'match_id': 0,  # Будет заполнено позже
            'cumulative_wins': 0,
            'cumulative_losses': 0,
            'streak': 0,
            'court_wins': 0,
            'court_losses': 0,
            'wins_last_5': 0,
            'wins_last_30d': 0,
            'matches_last_30d': 0,
            'win_rt': 0.0,
            'court_win_rt': 0.0,
            'win_rt_last_30': 0.0
        }
        player_stats_cache[player_name] = default_stats
        return default_stats


def update_player_cache(player_stats_cache, player_last_5_matches, player_name, match_result, match_date, court_type):
    """
    Обновляет кешированную статистику игрока с учетом результата матча
    """
    if player_name not in player_stats_cache:
        raise ValueError(f"Игрок {player_name} отсутствует в кеше")

    stats = player_stats_cache[player_name].copy()

    # Обновляем накопительные показатели
    stats['cumulative_wins'] += match_result
    stats['cumulative_losses'] += (1 - match_result)

    # Обновляем streak
    if match_result == 1:  # Победа
        stats['streak'] = 1 if stats['streak'] < 0 else stats['streak'] + 1
    else:  # Поражение
        stats['streak'] = -1 if stats['streak'] > 0 else stats['streak'] - 1

    # Обновляем статистику по корту
    if court_type == stats['court']:
        stats['court_wins'] += match_result
        stats['court_losses'] += (1 - match_result)
    else:
        # Если сменился тип корта
        stats['court'] = court_type
        stats['court_wins'] = match_result
        stats['court_losses'] = 1 - match_result

    # Обновляем историю последних 5 матчей
    if player_name not in player_last_5_matches:
        player_last_5_matches[player_name] = []

    player_last_5_matches[player_name].append({
        'date': match_date,
        'result': match_result
    })

    # Сортируем и оставляем только последние 5
    player_last_5_matches[player_name] = sorted(
        player_last_5_matches[player_name],
        key=lambda x: x['date']
    )[-5:]

    # Обновляем wins_last_5
    stats['wins_last_5'] = sum(match['result'] for match in player_last_5_matches[player_name])

    # Обновляем статистику за 30 дней
    thirty_days_ago = match_date - pd.Timedelta(days=30)

    # Фильтруем матчи за последние 30 дней
    recent_matches = [m for m in player_last_5_matches[player_name] if m['date'] >= thirty_days_ago]

    # Обновляем статистику последних 30 дней
    stats['matches_last_30d'] = len(recent_matches)
    stats['wins_last_30d'] = sum(m['result'] for m in recent_matches)

    # Пересчитываем производные показатели
    if stats['cumulative_losses'] > 0:
        stats['win_rt'] = stats['cumulative_wins'] / stats['cumulative_losses']
    else:
        stats['win_rt'] = 1.0 if stats['cumulative_wins'] > 0 else 0.0

    if stats['court_losses'] > 0:
        stats['court_win_rt'] = stats['court_wins'] / stats['court_losses']
    else:
        stats['court_win_rt'] = 1.0 if stats['court_wins'] > 0 else 0.0

    if stats['matches_last_30d'] > 0:
        stats['win_rt_last_30'] = stats['wins_last_30d'] / stats['matches_last_30d']
    else:
        stats['win_rt_last_30'] = 0.0

    # Обновляем запись в кеше
    player_stats_cache[player_name] = stats