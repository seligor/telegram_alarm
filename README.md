# telegram_alarm
Этот бот служит для оповещения групп пользователей о каких-либо событиях.
Например: есть потребность прислать сообщение нескольким пользователям одновременно, при этом нет возможности или желания создавать для этого групповой чат
Таким образом пользователи, подключаясь к боту вводят 9-значный номер группы оповещения и бот будет отправлять оповещения только тем, кто находится с ними в одной группе, делая это в личных сообщениях. 
Пример того, почему есть смысл его использовать: в обычном групповом чате может достаточно активно идти переписка, а значит зачастую звуковые уведомления в нём отключены. Для бота можно оставить звуковые оповещения - в него попадёт всё самое важное

При первом подключении нужно отправить боту команду /change_grp и он запросит ввести 9-значный номер группы оповещения. Данные о принадлежности к группам оповещения запишутся в sqlite базу данных. Как вы понимаете таких групп может быть до милиарда. 
Попадание случайных пользователей в группу оповещения маловероятно, но и это решаемо следующей версией бота, которая уже готовится. 
