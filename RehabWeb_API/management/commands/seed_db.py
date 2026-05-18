"""
Datos demo para probar el módulo 5 del frontend RehabWeb.

Se ejecuta vía `python manage.py seed_db`.

Es idempotente: identifica sus registros con `external_id` que empieza por
`DEMO-` y los reemplaza en cada corrida.
"""

from datetime import timedelta
from decimal import Decimal
from random import Random

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from RehabWeb_API.models import (
    ClinicalStatus,
    InactivityAlert,
    MetricPoint,
    Patient,
    Session,
    SessionExercise,
    Therapist,
    TherapistPatient,
)

class Command(BaseCommand):
    help = 'Genera datos demo para probar el módulo 5 del frontend RehabWeb.'

    def handle(self, *args, **options):
        DEMO_PREFIX = "DEMO-"
        rng = Random(42)
        now = timezone.now()

        def step(msg):
            self.stdout.write(f"  • {msg}")

        # ---------------------------------------------------------------------------
        # 1) Definición del Equipo
        # ---------------------------------------------------------------------------
        TEAM_USERS = [
            {'username': 'fisio', 'email': '', 'password': '123456'},
            {'username': 'eduardo', 'email': 'pm202350827@alm.buap.mx', 'password': '123456'},
            {'username': 'dafne', 'email': 'dafnecirnehernandez15@gmail.com', 'password': '123456'},
            {'username': 'herson', 'email': 'uc202358429@alm.buap.mx', 'password': '123456'},
            {'username': 'jessica', 'email': 'ch202323012@alm.buap.mx', 'password': '123456'},
            {'username': 'jocelyn', 'email': 'jocelynharo32@gmail.com', 'password': '123456'},
            {'username': 'luis', 'email': 'Oh202341121@alm.buap.mx', 'password': '123456'},
            {'username': 'quecholac', 'email': 'quecholac123@ejemplo.com', 'password': '123456'},
        ]

        # ---------------------------------------------------------------------------
        # 2) Limpieza de demos previas
        # ---------------------------------------------------------------------------
        with transaction.atomic():
            demos = Patient.objects.filter(external_id__startswith=DEMO_PREFIX)
            n = demos.count()
            if n:
                self.stdout.write(f"\nBorrando {n} pacientes demo previos (en cascada)...")
                demos.delete()
            
            # Limpiamos alertas demo asociadas a los usuarios del equipo
            usernames = [u['username'] for u in TEAM_USERS]
            InactivityAlert.objects.filter(therapist__user__username__in=usernames).delete()

        # ---------------------------------------------------------------------------
        # 3) Plantilla de Pacientes
        # ---------------------------------------------------------------------------
        PATIENTS_TEMPLATE = [
            {
                "id_suffix": "001",
                "full_name": "María González",
                "diagnosis": "Post-quirúrgico rodilla derecha (LCA)",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 1,
                "sessions_count": 28,
                "exercise_set": [
                    ("Flexión de rodilla", 3, 12),
                    ("Extensión cuádriceps", 3, 15),
                    ("Sentadilla isométrica", 4, 20),
                    ("Step-up con apoyo", 3, 10),
                    ("Prensa de piernas leve", 3, 12),
                ],
                "adherence_range": (78, 92),
                "score_range": (Decimal("6.5"), Decimal("8.8")),
                "rom_progress": (45, 110),
                "duration_range": (40, 60),
            },
            {
                "id_suffix": "002",
                "full_name": "Carlos Ramírez",
                "diagnosis": "Capsulitis adhesiva (hombro congelado)",
                "status": ClinicalStatus.RIESGO,
                "last_session_days_ago": 8,
                "sessions_count": 14,
                "exercise_set": [
                    ("Pendulares de hombro", 3, 15),
                    ("Rotación externa con banda", 3, 12),
                    ("Elevación lateral asistida", 3, 10),
                    ("Movilización escapular", 2, 20),
                ],
                "adherence_range": (50, 70),
                "score_range": (Decimal("4.5"), Decimal("6.2")),
                "rom_progress": (60, 85),
                "duration_range": (30, 45),
            },
            {
                "id_suffix": "003",
                "full_name": "Lucía Fernández",
                "diagnosis": "Lumbalgia crónica mecánica",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 2,
                "sessions_count": 25,
                "exercise_set": [
                    ("Plancha frontal", 3, 30),
                    ("Puente glúteo", 4, 15),
                    ("Gato-camello", 2, 12),
                    ("Estiramiento isquiotibial", 2, 30),
                    ("Bird-dog", 3, 10),
                ],
                "adherence_range": (80, 95),
                "score_range": (Decimal("7.0"), Decimal("9.1")),
                "rom_progress": (50, 105),
                "duration_range": (45, 60),
            },
            {
                "id_suffix": "004",
                "full_name": "Diego Torres",
                "diagnosis": "Epicondilitis lateral (codo de tenista)",
                "status": ClinicalStatus.RIESGO,
                "last_session_days_ago": 20,
                "sessions_count": 12,
                "exercise_set": [
                    ("Estiramiento epicondíleos", 3, 20),
                    ("Fortalecimiento con pesa 1 kg", 3, 12),
                    ("Excéntricos de muñeca", 3, 10),
                ],
                "adherence_range": (45, 65),
                "score_range": (Decimal("4.5"), Decimal("6.8")),
                "rom_progress": (55, 75),
                "duration_range": (25, 40),
            },
            {
                "id_suffix": "005",
                "full_name": "Ana Martínez",
                "diagnosis": "Esguince grado II de tobillo izquierdo",
                "status": ClinicalStatus.ALTA,
                "last_session_days_ago": 45,
                "sessions_count": 18,
                "exercise_set": [
                    ("Propiocepción con bosu", 3, 30),
                    ("Tobillera con banda", 3, 15),
                    ("Marcha en talones", 2, 20),
                    ("Salto unipodal controlado", 3, 8),
                ],
                "adherence_range": (85, 98),
                "score_range": (Decimal("8.0"), Decimal("9.5")),
                "rom_progress": (70, 120),
                "duration_range": (35, 50),
            },
            {
                "id_suffix": "006",
                "full_name": "Roberto Jiménez",
                "diagnosis": "Ruptura del manguito rotador (Post-op)",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 3,
                "sessions_count": 30,
                "exercise_set": [
                    ("Elevación pasiva con polea", 3, 15),
                    ("Rotación interna isométrica", 3, 10),
                    ("Estiramiento cápsula posterior", 3, 20),
                    ("Abducción con toalla", 2, 12),
                ],
                "adherence_range": (75, 88),
                "score_range": (Decimal("6.0"), Decimal("8.5")),
                "rom_progress": (30, 90),
                "duration_range": (45, 60),
            },
            {
                "id_suffix": "007",
                "full_name": "Laura Gómez",
                "diagnosis": "Reemplazo total de cadera derecha",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 1,
                "sessions_count": 22,
                "exercise_set": [
                    ("Abducción de cadera de pie", 3, 12),
                    ("Extensión de cadera isométrica", 3, 15),
                    ("Marcha con andadera", 1, 10),
                    ("Deslizamiento de talón", 3, 10),
                ],
                "adherence_range": (82, 95),
                "score_range": (Decimal("7.5"), Decimal("9.2")),
                "rom_progress": (40, 95),
                "duration_range": (50, 65),
            },
            {
                "id_suffix": "008",
                "full_name": "Miguel Sánchez",
                "diagnosis": "Tendinopatía aquílea bilateral",
                "status": ClinicalStatus.RIESGO,
                "last_session_days_ago": 12,
                "sessions_count": 10,
                "exercise_set": [
                    ("Excéntrico en escalón", 3, 15),
                    ("Estiramiento gastrocnemio", 3, 30),
                    ("Elevación de talones sentado", 4, 12),
                ],
                "adherence_range": (40, 60),
                "score_range": (Decimal("4.0"), Decimal("6.0")),
                "rom_progress": (15, 30),
                "duration_range": (30, 45),
            },
            {
                "id_suffix": "009",
                "full_name": "Carmen Ruiz",
                "diagnosis": "Síndrome facetario lumbar",
                "status": ClinicalStatus.ALTA,
                "last_session_days_ago": 60,
                "sessions_count": 16,
                "exercise_set": [
                    ("Inclinación pélvica", 3, 15),
                    ("Rodillas al pecho", 3, 20),
                    ("Estiramiento piramidal", 2, 30),
                    ("Fortalecimiento core isométrico", 3, 12),
                ],
                "adherence_range": (80, 95),
                "score_range": (Decimal("7.8"), Decimal("9.5")),
                "rom_progress": (50, 90),
                "duration_range": (40, 50),
            },
            {
                "id_suffix": "010",
                "full_name": "Pedro Álvarez",
                "diagnosis": "Fascitis plantar aguda",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 2,
                "sessions_count": 11,
                "exercise_set": [
                    ("Rodamiento con botella fría", 1, 5),
                    ("Estiramiento fascia con toalla", 3, 20),
                    ("Recoger canicas con dedos", 3, 15),
                ],
                "adherence_range": (70, 85),
                "score_range": (Decimal("6.5"), Decimal("8.0")),
                "rom_progress": (0, 0), # No aplica ROM extenso
                "duration_range": (20, 35),
            },
            {
                "id_suffix": "011",
                "full_name": "Sofía Castro",
                "diagnosis": "Síndrome del túnel carpiano",
                "status": ClinicalStatus.RIESGO,
                "last_session_days_ago": 15,
                "sessions_count": 14,
                "exercise_set": [
                    ("Deslizamiento del nervio mediano", 3, 10),
                    ("Extensión de muñeca", 3, 15),
                    ("Apretón de pelota terapéutica", 3, 20),
                ],
                "adherence_range": (60, 75),
                "score_range": (Decimal("5.5"), Decimal("7.0")),
                "rom_progress": (40, 60),
                "duration_range": (25, 40),
            },
            {
                "id_suffix": "012",
                "full_name": "Javier Morales",
                "diagnosis": "Cervicalgia por latigazo cervical",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 1,
                "sessions_count": 21,
                "exercise_set": [
                    ("Retracción cervical", 3, 10),
                    ("Estiramiento trapecio", 3, 20),
                    ("Rotación cervical activa", 2, 15),
                    ("Isométricos cuello", 4, 5),
                ],
                "adherence_range": (75, 90),
                "score_range": (Decimal("6.8"), Decimal("8.5")),
                "rom_progress": (30, 75),
                "duration_range": (35, 50),
            },
            {
                "id_suffix": "013",
                "full_name": "Teresa Gil",
                "diagnosis": "Osteoartritis de rodilla bilateral",
                "status": ClinicalStatus.RIESGO,
                "last_session_days_ago": 18,
                "sessions_count": 19,
                "exercise_set": [
                    ("Bicicleta estática", 1, 15),
                    ("Elevación pierna extendida", 3, 12),
                    ("Deslizamiento en pared", 3, 10),
                ],
                "adherence_range": (35, 55),
                "score_range": (Decimal("3.5"), Decimal("5.5")),
                "rom_progress": (40, 70),
                "duration_range": (30, 45),
            },
            {
                "id_suffix": "014",
                "full_name": "Raúl Vargas",
                "diagnosis": "Luxación anterior de hombro (Recidivante)",
                "status": ClinicalStatus.ACTIVO,
                "last_session_days_ago": 4,
                "sessions_count": 26,
                "exercise_set": [
                    ("Estabilización rítmica", 3, 15),
                    ("Rotación interna con polea", 3, 12),
                    ("Flexiones contra pared", 3, 15),
                    ("Remo con banda elástica", 4, 10),
                ],
                "adherence_range": (85, 95),
                "score_range": (Decimal("8.0"), Decimal("9.5")),
                "rom_progress": (50, 130),
                "duration_range": (45, 60),
            },
            {
                "id_suffix": "015",
                "full_name": "Elena Rojas",
                "diagnosis": "Fractura de Colles (Post-inmovilización)",
                "status": ClinicalStatus.ALTA,
                "last_session_days_ago": 70,
                "sessions_count": 24,
                "exercise_set": [
                    ("Pronosupinación activa", 3, 15),
                    ("Flexoextensión de muñeca", 3, 20),
                    ("Masaje cicatrizal", 1, 5),
                    ("Fuerza de agarre con masilla", 3, 10),
                ],
                "adherence_range": (88, 100),
                "score_range": (Decimal("8.5"), Decimal("9.8")),
                "rom_progress": (20, 80),
                "duration_range": (40, 55),
            },
        ]

        def jitter(base, dlt=2):
            return base + rng.randint(-dlt, dlt)

        def session_at(days_ago):
            return now - timedelta(days=days_ago, hours=rng.randint(0, 6), minutes=rng.randint(0, 59))

        # ---------------------------------------------------------------------------
        # Observaciones Clínicas Realistas
        # ---------------------------------------------------------------------------
        OBSERVATIONS_GOOD = [
            "Sin incidencias. Tolera la carga progresiva adecuadamente.",
            "Mejora notable en el rango articular comparado con la sesión anterior.",
            "El paciente refiere disminución del dolor al realizar los ejercicios excéntricos.",
            "Excelente adherencia al tratamiento en casa. Postura corregida.",
            "Movilidad articular sin restricciones evidentes. Se avanza a fase de fortalecimiento.",
            "El paciente completa las series sin presentar fatiga temprana.",
            "Inflamación reducida en la zona afectada. Buena respuesta al tratamiento manual.",
        ]
        
        OBSERVATIONS_NEUTRAL = [
            "Refiere dolor 2/10 al final de la sesión. Se aplica crioterapia.",
            "Fatiga muscular esperada en las últimas repeticiones.",
            "Se requiere corrección verbal para la postura durante las sentadillas.",
            "Ligera molestia en el rango máximo de flexión. Se adapta la carga.",
            "Sesión completada con pausas de descanso más largas de lo habitual.",
        ]

        OBSERVATIONS_BAD = [
            "Dolor agudo (6/10) al intentar rotación. Se suspende el ejercicio.",
            "Se reduce la intensidad por dolor inflamatorio recurrente.",
            "Paciente reporta no haber realizado los ejercicios en casa.",
            "Marcha claudicante persistente. No tolera la carga completa.",
            "Rigidez matutina severa reportada. Rango de movimiento limitado hoy.",
        ]

        # ---------------------------------------------------------------------------
        # 4) Generación por Terapeuta
        # ---------------------------------------------------------------------------
        User = get_user_model()

        for t_data in TEAM_USERS:
            self.stdout.write(f"\nProcesando terapeuta: {t_data['username']}...")
            
            # Crear o recuperar usuario
            user, created = User.objects.get_or_create(
                username=t_data['username'], 
                defaults={'email': t_data['email']}
            )
            
            # Asegurar contraseña
            user.set_password(t_data['password'])
            user.save()

            therapist, _ = Therapist.objects.get_or_create(user=user)

            for p in PATIENTS_TEMPLATE:
                # Hacemos el ID externo único por terapeuta (ej: DEMO-eduardo-001)
                ext_id = f"{DEMO_PREFIX}{t_data['username']}-{p['id_suffix']}"
                
                patient = Patient.objects.create(
                    external_id=ext_id,
                    full_name=p["full_name"],
                )
                TherapistPatient.objects.create(
                    therapist=therapist,
                    patient=patient,
                    primary_diagnosis=p["diagnosis"],
                    clinical_status=p["status"],
                )
                step(f"Asignado: {patient.full_name} ({p['status']}) - {p['sessions_count']} sesiones")

                # ---- Sesiones ----
                last_days = p["last_session_days_ago"]
                sessions = []
                for i in range(p["sessions_count"]):
                    # Calculamos los días atrás para generar la sesión (en reversa)
                    days_ago = last_days + i * rng.randint(2, 4)
                    
                    # Selección de observación según el estado y probabilidad
                    if p["status"] == ClinicalStatus.RIESGO:
                        obs_note = rng.choice(OBSERVATIONS_BAD + OBSERVATIONS_NEUTRAL)
                    elif p["status"] == ClinicalStatus.ALTA:
                        obs_note = rng.choice(OBSERVATIONS_GOOD)
                    else:
                        r = rng.random()
                        if r < 0.6:
                            obs_note = rng.choice(OBSERVATIONS_GOOD)
                        elif r < 0.9:
                            obs_note = rng.choice(OBSERVATIONS_NEUTRAL)
                        else:
                            obs_note = rng.choice(OBSERVATIONS_BAD)

                    s = Session.objects.create(
                        patient=patient,
                        therapist=therapist,
                        occurred_at=session_at(days_ago),
                        program_label=f"Programa rehabilitación — semana {p['sessions_count'] - i}",
                        duration_min=rng.randint(*p["duration_range"]),
                        score=Decimal(
                            rng.uniform(float(p["score_range"][0]), float(p["score_range"][1]))
                        ).quantize(Decimal("0.01")),
                        status="completada" if rng.random() < 0.85 else rng.choice(["parcial", "interrumpida"]),
                        adherence_percent=rng.randint(*p["adherence_range"]),
                        notes=obs_note,
                    )
                    sessions.append(s)

                    # Ejercicios de la sesión
                    for order, (name, sets, reps) in enumerate(p["exercise_set"]):
                        SessionExercise.objects.create(
                            session=s,
                            name=name,
                            sets=sets,
                            reps=jitter(reps, 2),
                            sort_order=order,
                            notes="",
                        )

                # ---- MetricPoint: ROM semanal ----
                rom_start, rom_end = p["rom_progress"]
                weeks = min(12, max(4, p["sessions_count"] // 2)) # Ajustar semanas al volumen de sesiones
                for w in range(weeks):
                    frac = w / (weeks - 1)
                    meta = rom_start + (rom_end - rom_start) * frac
                    observed = meta - rng.uniform(0, 8)
                    MetricPoint.objects.create(
                        patient=patient,
                        metric_type=MetricPoint.MetricType.ROM_WEEK,
                        period_label=f"Semana {w + 1}",
                        sort_order=w,
                        meta_value=Decimal(meta).quantize(Decimal("0.001")),
                        observed_value=Decimal(observed).quantize(Decimal("0.001")),
                    )

                # ---- MetricPoint: serie temporal ----
                temporal_points = min(15, p["sessions_count"])
                base_meta = Decimal("70.0")
                for t in range(temporal_points):
                    progress = Decimal(t) * Decimal("3.5")
                    meta = base_meta + progress
                    if p["status"] == ClinicalStatus.RIESGO:
                        obs = meta - Decimal(str(rng.uniform(8, 18)))
                    elif p["status"] == ClinicalStatus.ALTA:
                        obs = meta + Decimal(str(rng.uniform(-2, 4)))
                    else:
                        obs = meta - Decimal(str(rng.uniform(2, 8)))
                        
                    MetricPoint.objects.create(
                        patient=patient,
                        metric_type=MetricPoint.MetricType.TEMPORAL,
                        period_label=f"T{t + 1}",
                        sort_order=t,
                        meta_value=meta.quantize(Decimal("0.001")),
                        observed_value=obs.quantize(Decimal("0.001")),
                    )

        # ---------------------------------------------------------------------------
        # 5) Refresh de alertas de inactividad
        # ---------------------------------------------------------------------------
        self.stdout.write("\nEjecutando `refresh_inactivity_alerts` (lógica real del módulo 5)…")
        call_command("refresh_inactivity_alerts")

        # ---------------------------------------------------------------------------
        # 6) Resumen
        # ---------------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\nResumen final de la base de datos:"))
        self.stdout.write(f"  Pacientes demo totales : {Patient.objects.filter(external_id__startswith=DEMO_PREFIX).count()}")
        self.stdout.write(f"  Usuarios terapeutas    : {len(TEAM_USERS)}")
        self.stdout.write(f"  Sesiones totales       : {Session.objects.filter(patient__external_id__startswith=DEMO_PREFIX).count()}")
        self.stdout.write(f"  Alertas totales        : {InactivityAlert.objects.filter(patient__external_id__startswith=DEMO_PREFIX).count()}")
        self.stdout.write(self.style.SUCCESS("\nListo. Cada integrante ya puede hacer login con su usuario y la contraseña 123456."))
