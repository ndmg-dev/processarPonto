import json

with open('app/storage/uploads/3e7b3cf2-cfc7-4cdc-aca5-b67f3ae3b25f.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for emp in data['employees'][:3]:
    print("=" * 80)
    print("Colaborador:", emp['name'])
    print("-" * 80)
    
    # Summary
    summary = emp.get('summary', {})
    print("RESUMO:")
    print("  Horas 50%:", summary.get('overtime_50', '—'))
    print("  Horas 100%:", summary.get('overtime_100', '—'))
    print("  Faltas:", summary.get('absences', '—'))
    print("  Atrasos:", summary.get('delays', '—'))
    print("  DSR Descontado:", summary.get('dsr_discount', '—'))
    print()
    
    # Show some key days
    check_dates = ['27/05', '28/05', '31/05', '01/06', '02/06', '06/06', '07/06', '08/06']
    for r in emp['records']:
        if r['date'] in check_dates:
            e1 = r['first_period_entry'] or '—'
            s1 = r['first_period_exit'] or '—'
            e2 = r['second_period_entry'] or '—'
            s2 = r['second_period_exit'] or '—'
            status = r['status']
            print("  {} {} | {} | {} | {} | {} | {}".format(
                r['weekday'], r['date'], e1, s1, e2, s2, status
            ))
    print()
