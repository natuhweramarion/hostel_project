"""
Management command: seed_data
Creates realistic demo data for the Hostel Management System.

Usage:
    python manage.py seed_data            # Create data (skips if already exists)
    python manage.py seed_data --flush    # Wipe all non-superuser data first, then seed

What is created:
    - 3 hostels  (1 Male, 1 Female, 1 Mixed)
    - 6 blocks   (2 per hostel)
    - 30 rooms   (5 per block, varied types and capacities)
    - 2 managers (male warden + female warden)
    - 20 students (10 male, 10 female, realistic Ugandan names)
    - 16 allocations (active + a few past)
    - 22 payments (verified, pending, rejected - across two academic years)
    - 5 booking requests (pending + reviewed)
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from allocations.models import Allocation, BookingRequest
from hostels.models import Block, Hostel, Room
from payments.models import Payment

User = get_user_model()

# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

HOSTELS = [
    {
        "name": "Nsibirwa Hall",
        "location": "North Campus, near the Main Gate",
        "gender": "Male",
        "description": (
            "Nsibirwa Hall is a well-established male hostel offering comfortable "
            "accommodation for undergraduate students. Named after Martin Luther Nsibirwa, "
            "the hall features study rooms, a common room, and reliable Wi-Fi."
        ),
        "price_per_semester": Decimal("850000"),
        "blocks": [
            {
                "name": "Block A",
                "description": "Ground and first floor - single and double rooms",
                "rooms": [
                    ("A101", "Single",        1, Decimal("850000")),
                    ("A102", "Double",        2, Decimal("750000")),
                    ("A103", "Double",        2, Decimal("750000")),
                    ("A104", "Self-Contained",1, Decimal("950000")),
                    ("A105", "Shared",        4, Decimal("600000")),
                ],
            },
            {
                "name": "Block B",
                "description": "Second and third floor - shared and self-contained rooms",
                "rooms": [
                    ("B101", "Shared",        4, Decimal("600000")),
                    ("B102", "Shared",        4, Decimal("600000")),
                    ("B103", "Double",        2, Decimal("750000")),
                    ("B104", "Self-Contained",1, Decimal("950000")),
                    ("B105", "Single",        1, Decimal("850000")),
                ],
            },
        ],
    },
    {
        "name": "Mary Stuart Hall",
        "location": "South Campus, adjacent to the Library",
        "gender": "Female",
        "description": (
            "Mary Stuart Hall is the premier female hostel on campus, offering a safe and "
            "nurturing environment for female students. The hall includes a laundry room, "
            "reading lounge, and 24-hour security."
        ),
        "price_per_semester": Decimal("800000"),
        "blocks": [
            {
                "name": "Block A",
                "description": "Lower block - self-contained and single rooms",
                "rooms": [
                    ("A101", "Self-Contained",1, Decimal("900000")),
                    ("A102", "Self-Contained",1, Decimal("900000")),
                    ("A103", "Single",        1, Decimal("800000")),
                    ("A104", "Double",        2, Decimal("720000")),
                    ("A105", "Shared",        4, Decimal("580000")),
                ],
            },
            {
                "name": "Block B",
                "description": "Upper block - shared and double rooms",
                "rooms": [
                    ("B101", "Shared",        4, Decimal("580000")),
                    ("B102", "Shared",        4, Decimal("580000")),
                    ("B103", "Double",        2, Decimal("720000")),
                    ("B104", "Double",        2, Decimal("720000")),
                    ("B105", "Single",        1, Decimal("800000")),
                ],
            },
        ],
    },
    {
        "name": "Mitchell Hall",
        "location": "East Campus, near the Faculty of Technology",
        "gender": "Mixed",
        "description": (
            "Mitchell Hall is a modern mixed-gender hostel designed for postgraduate and "
            "international students. Each floor has dedicated male and female wings with "
            "shared common areas, high-speed internet, and en-suite bathrooms."
        ),
        "price_per_semester": Decimal("1100000"),
        "blocks": [
            {
                "name": "Block A",
                "description": "Male wing - floors 1 and 2",
                "rooms": [
                    ("A101", "Self-Contained",1, Decimal("1100000")),
                    ("A102", "Self-Contained",1, Decimal("1100000")),
                    ("A103", "Double",        2, Decimal("950000")),
                    ("A104", "Double",        2, Decimal("950000")),
                    ("A105", "Single",        1, Decimal("1050000")),
                ],
            },
            {
                "name": "Block B",
                "description": "Female wing - floors 3 and 4",
                "rooms": [
                    ("B101", "Self-Contained",1, Decimal("1100000")),
                    ("B102", "Self-Contained",1, Decimal("1100000")),
                    ("B103", "Double",        2, Decimal("950000")),
                    ("B104", "Double",        2, Decimal("950000")),
                    ("B105", "Shared",        3, Decimal("820000")),
                ],
            },
        ],
    },
]

MANAGERS = [
    {
        "username": "warden_male",
        "first_name": "Ssemakula",
        "last_name": "Patrick",
        "email": "warden.male@hostel.ac.ug",
        "phone_number": "+256772100001",
        "gender": "Male",
    },
    {
        "username": "warden_female",
        "first_name": "Namutebi",
        "last_name": "Agnes",
        "email": "warden.female@hostel.ac.ug",
        "phone_number": "+256772100002",
        "gender": "Female",
    },
]

MALE_STUDENTS = [
    ("mukasa_john",   "Mukasa",   "John",    "mukasa.john@students.ac.ug",   "2024/STU/001", "Computer Science",       "300", "+256701100001", date(2002,  3, 15)),
    ("kato_brian",    "Kato",     "Brian",   "kato.brian@students.ac.ug",    "2024/STU/002", "Electrical Engineering", "200", "+256701100002", date(2003,  7, 22)),
    ("lubega_peter",  "Lubega",   "Peter",   "lubega.peter@students.ac.ug",  "2024/STU/003", "Business Administration","400", "+256701100003", date(2001, 11,  5)),
    ("nsubuga_paul",  "Nsubuga",  "Paul",    "nsubuga.paul@students.ac.ug",  "2024/STU/004", "Law",                    "100", "+256701100004", date(2005,  1, 30)),
    ("wasswa_eman",   "Wasswa",   "Emmanuel","wasswa.eman@students.ac.ug",   "2024/STU/005", "Medicine & Surgery",     "200", "+256701100005", date(2004,  6, 18)),
    ("mawejje_rob",   "Mawejje",  "Robert",  "mawejje.rob@students.ac.ug",   "2024/STU/006", "Computer Science",       "100", "+256701100006", date(2005,  9, 12)),
    ("kabugo_fran",   "Kabugo",   "Francis", "kabugo.fran@students.ac.ug",   "2024/STU/007", "Agriculture",            "300", "+256701100007", date(2002,  4, 25)),
    ("ssenabulya_t",  "Ssenabulya","Timothy","ssenabulya.t@students.ac.ug",  "2024/STU/008", "Social Sciences",        "400", "+256701100008", date(2001,  8,  3)),
    ("mutebi_col",    "Mutebi",   "Collins", "mutebi.col@students.ac.ug",    "2024/STU/009", "Education",              "200", "+256701100009", date(2003,  2, 14)),
    ("ssali_dan",     "Ssali",    "Daniel",  "ssali.dan@students.ac.ug",     "2024/STU/010", "Architecture",           "300", "+256701100010", date(2002, 12,  7)),
]

FEMALE_STUDENTS = [
    ("nakato_sarah",  "Nakato",   "Sarah",   "nakato.sarah@students.ac.ug",  "2024/STU/011", "Computer Science",       "300", "+256702200001", date(2002,  5, 20)),
    ("namutebi_gra",  "Namutebi", "Grace",   "namutebi.gra@students.ac.ug",  "2024/STU/012", "Medicine & Surgery",     "400", "+256702200002", date(2001,  9, 11)),
    ("namukasa_joy",  "Namukasa", "Joyce",   "namukasa.joy@students.ac.ug",  "2024/STU/013", "Law",                    "200", "+256702200003", date(2003,  3, 28)),
    ("apio_susan",    "Apio",     "Susan",   "apio.susan@students.ac.ug",    "2024/STU/014", "Business Administration","100", "+256702200004", date(2005,  7,  4)),
    ("akello_mary",   "Akello",   "Mary",    "akello.mary@students.ac.ug",   "2024/STU/015", "Education",              "300", "+256702200005", date(2002, 10, 16)),
    ("nabakooza_p",   "Nabakooza","Priscilla","nabakooza.p@students.ac.ug",  "2024/STU/016", "Social Sciences",        "200", "+256702200006", date(2003,  1,  9)),
    ("nassali_ann",   "Nassali",  "Annet",   "nassali.ann@students.ac.ug",   "2024/STU/017", "Architecture",           "400", "+256702200007", date(2001,  6, 23)),
    ("nankya_fat",    "Nankya",   "Fatima",  "nankya.fat@students.ac.ug",    "2024/STU/018", "Agriculture",            "100", "+256702200008", date(2005,  4,  1)),
    ("nakirya_dor",   "Nakirya",  "Doreen",  "nakirya.dor@students.ac.ug",   "2024/STU/019", "Electrical Engineering", "300", "+256702200009", date(2002,  8, 30)),
    ("mutesi_vio",    "Mutesi",   "Violet",  "mutesi.vio@students.ac.ug",    "2024/STU/020", "Computer Science",       "200", "+256702200010", date(2003, 11, 17)),
]

PAYMENT_METHODS = ["Bank Transfer", "Mobile Money (MTN)", "Mobile Money (Airtel)", "Bank Transfer", "Mobile Money (MTN)"]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ref(prefix, n):
    return f"{prefix}{n:06d}"


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Populate the database with realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all non-superuser data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        if Hostel.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Data already exists. Run with --flush to reset. Skipping."
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding demo data ===\n"))

        # 1 - Infrastructure
        hostels = self._create_hostels()

        # 2 - Staff
        manager = self._create_managers()

        # 3 - Students
        male_students, female_students = self._create_students()

        # 4 - Allocations
        self._create_allocations(hostels, male_students, female_students)

        # 5 - Payments
        self._create_payments(male_students, female_students, manager)

        # 6 - Booking requests
        self._create_booking_requests(hostels, male_students, female_students, manager)

        self._print_summary()

    # -----------------------------------------------------------------------
    # Flush
    # -----------------------------------------------------------------------

    def _flush(self):
        self.stdout.write("  Flushing existing data (preserving superusers)...")
        Payment.objects.all().delete()
        BookingRequest.objects.all().delete()
        Allocation.objects.all().delete()
        Room.objects.all().delete()
        Block.objects.all().delete()
        Hostel.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS("  OK Flush complete\n"))

    # -----------------------------------------------------------------------
    # Hostels, Blocks, Rooms
    # -----------------------------------------------------------------------

    def _create_hostels(self):
        result = {}
        for hdata in HOSTELS:
            hostel = Hostel.objects.create(
                name=hdata["name"],
                location=hdata["location"],
                gender=hdata["gender"],
                description=hdata["description"],
                price_per_semester=hdata["price_per_semester"],
            )
            result[hdata["name"]] = hostel

            for bdata in hdata["blocks"]:
                block = Block.objects.create(
                    hostel=hostel,
                    name=bdata["name"],
                    description=bdata["description"],
                )
                for room_number, room_type, capacity, price in bdata["rooms"]:
                    Room.objects.create(
                        block=block,
                        room_number=room_number,
                        room_type=room_type,
                        capacity=capacity,
                        price_per_semester=price,
                    )

        hostel_count = Hostel.objects.count()
        block_count = Block.objects.count()
        room_count = Room.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"  OK {hostel_count} hostels, {block_count} blocks, {room_count} rooms")
        )
        return result

    # -----------------------------------------------------------------------
    # Managers
    # -----------------------------------------------------------------------

    def _create_managers(self):
        managers = []
        for mdata in MANAGERS:
            mgr, created = User.objects.get_or_create(
                username=mdata["username"],
                defaults={
                    "first_name": mdata["first_name"],
                    "last_name": mdata["last_name"],
                    "email": mdata["email"],
                    "phone_number": mdata["phone_number"],
                    "gender": mdata["gender"],
                    "is_manager": True,
                    "is_staff": True,
                },
            )
            if created:
                mgr.set_password("manager@2025")
                mgr.save()
            managers.append(mgr)

        self.stdout.write(self.style.SUCCESS(f"  OK {len(managers)} managers created"))
        return managers[0]  # return primary manager for payment verification

    # -----------------------------------------------------------------------
    # Students
    # -----------------------------------------------------------------------

    def _create_students(self):
        male_students = []
        female_students = []

        for username, last, first, email, sid, dept, level, phone, dob in MALE_STUDENTS:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "student_id": sid,
                    "department": dept,
                    "level": level,
                    "phone_number": phone,
                    "date_of_birth": dob,
                    "gender": "Male",
                    "is_student": True,
                },
            )
            if created:
                u.set_password("student@2025")
                u.save()
            male_students.append(u)

        for username, last, first, email, sid, dept, level, phone, dob in FEMALE_STUDENTS:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "student_id": sid,
                    "department": dept,
                    "level": level,
                    "phone_number": phone,
                    "date_of_birth": dob,
                    "gender": "Female",
                    "is_student": True,
                },
            )
            if created:
                u.set_password("student@2025")
                u.save()
            female_students.append(u)

        self.stdout.write(self.style.SUCCESS(
            f"  OK {len(male_students)} male students, {len(female_students)} female students"
        ))
        return male_students, female_students

    # -----------------------------------------------------------------------
    # Allocations
    # -----------------------------------------------------------------------

    def _create_allocations(self, hostels, male_students, female_students):
        """
        Allocation plan:
          - Nsibirwa Hall (Male) : 7 male students (6 active, 1 past)
          - Mary Stuart Hall (Female): 7 female students (6 active, 1 past)
          - Mitchell Hall (Mixed): 2 male + 2 female active students
        Total: 12 active + 4 past = 16 allocations
        """
        nsibirwa = hostels["Nsibirwa Hall"]
        mary_stuart = hostels["Mary Stuart Hall"]
        mitchell = hostels["Mitchell Hall"]

        # ---- Nsibirwa Hall (Male) ----
        n_block_a = nsibirwa.blocks.get(name="Block A")
        n_block_b = nsibirwa.blocks.get(name="Block B")
        n_rooms = list(n_block_a.rooms.all()) + list(n_block_b.rooms.all())

        # 6 active male allocations (skip room A105 shared - only 4 beds)
        active_male_rooms = [
            n_block_a.rooms.get(room_number="A101"),  # Single
            n_block_a.rooms.get(room_number="A102"),  # Double
            n_block_a.rooms.get(room_number="A102"),  # Double (2nd bed)
            n_block_a.rooms.get(room_number="A103"),  # Double
            n_block_b.rooms.get(room_number="B103"),  # Double
            n_block_b.rooms.get(room_number="B105"),  # Single
        ]
        for student, room in zip(male_students[:6], active_male_rooms):
            Allocation.objects.create(
                user=student,
                room=room,
                status="active",
                academic_year="2024/2025",
            )

        # 1 past male allocation (left last semester)
        past_male_room = n_block_b.rooms.get(room_number="B101")  # Shared
        past_alloc = Allocation.objects.create(
            user=male_students[6],
            room=past_male_room,
            status="left",
            academic_year="2023/2024",
        )
        past_alloc.date_left = timezone.now() - timedelta(days=180)
        past_alloc.save()

        # ---- Mary Stuart Hall (Female) ----
        ms_block_a = mary_stuart.blocks.get(name="Block A")
        ms_block_b = mary_stuart.blocks.get(name="Block B")

        active_female_rooms = [
            ms_block_a.rooms.get(room_number="A101"),  # Self-Contained
            ms_block_a.rooms.get(room_number="A103"),  # Single
            ms_block_a.rooms.get(room_number="A104"),  # Double
            ms_block_a.rooms.get(room_number="A104"),  # Double (2nd bed)
            ms_block_b.rooms.get(room_number="B103"),  # Double
            ms_block_b.rooms.get(room_number="B105"),  # Single
        ]
        for student, room in zip(female_students[:6], active_female_rooms):
            Allocation.objects.create(
                user=student,
                room=room,
                status="active",
                academic_year="2024/2025",
            )

        # 1 past female allocation
        past_female_room = ms_block_b.rooms.get(room_number="B102")  # Shared
        past_alloc_f = Allocation.objects.create(
            user=female_students[6],
            room=past_female_room,
            status="left",
            academic_year="2023/2024",
        )
        past_alloc_f.date_left = timezone.now() - timedelta(days=200)
        past_alloc_f.save()

        # ---- Mitchell Hall (Mixed) ----
        mt_block_a = mitchell.blocks.get(name="Block A")
        mt_block_b = mitchell.blocks.get(name="Block B")

        # 2 male students in Block A
        Allocation.objects.create(
            user=male_students[7],
            room=mt_block_a.rooms.get(room_number="A101"),
            status="active",
            academic_year="2024/2025",
        )
        Allocation.objects.create(
            user=male_students[8],
            room=mt_block_a.rooms.get(room_number="A103"),
            status="active",
            academic_year="2024/2025",
        )

        # 2 female students in Block B
        Allocation.objects.create(
            user=female_students[7],
            room=mt_block_b.rooms.get(room_number="B101"),
            status="active",
            academic_year="2024/2025",
        )
        Allocation.objects.create(
            user=female_students[8],
            room=mt_block_b.rooms.get(room_number="B103"),
            status="active",
            academic_year="2024/2025",
        )

        active_count = Allocation.objects.filter(status="active").count()
        total_count = Allocation.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"  OK {total_count} allocations ({active_count} active, {total_count - active_count} past)"
        ))

    # -----------------------------------------------------------------------
    # Payments
    # -----------------------------------------------------------------------

    def _create_payments(self, male_students, female_students, verifier):
        """
        Payment plan (22 payments):
          - All allocated students for 2024/2025: verified payment (full amount)
          - 5 students: second pending payment (current semester, partial)
          - 2 students: rejected payment (bad reference)
          - 2 students with past allocations: 1 old verified payment each
        """
        all_students = male_students + female_students
        now = timezone.now()

        HOSTEL_PRICES = {
            "Nsibirwa Hall":    Decimal("850000"),
            "Mary Stuart Hall": Decimal("800000"),
            "Mitchell Hall":    Decimal("1100000"),
        }

        # All currently active students get a verified payment
        active_allocs = (
            Allocation.objects
            .filter(status="active", academic_year="2024/2025")
            .select_related("user", "room__block__hostel")
        )
        for i, alloc in enumerate(active_allocs, start=1):
            hostel_name = alloc.room.block.hostel.name
            amount = HOSTEL_PRICES.get(hostel_name, Decimal("850000"))
            Payment.objects.create(
                user=alloc.user,
                amount=amount,
                reference_number=_ref("TXN2425", i),
                status="verified",
                academic_year="2024/2025",
                payment_method=PAYMENT_METHODS[i % len(PAYMENT_METHODS)],
                notes="Full semester fee payment.",
                verified_by=verifier,
                date_verified=now - timedelta(days=random.randint(10, 60)),
            )

        # 5 students have a pending partial payment for this semester
        pending_students = male_students[2:4] + female_students[2:5]
        for i, student in enumerate(pending_students, start=100):
            Payment.objects.create(
                user=student,
                amount=Decimal("500000"),
                reference_number=_ref("MMO2425", i),
                status="pending",
                academic_year="2024/2025",
                payment_method="Mobile Money (MTN)",
                notes="Partial payment - balance to follow.",
            )

        # 2 rejected payments
        rejected_students = [male_students[4], female_students[4]]
        for i, student in enumerate(rejected_students, start=200):
            Payment.objects.create(
                user=student,
                amount=Decimal("850000"),
                reference_number=_ref("REJ2425", i),
                status="rejected",
                academic_year="2024/2025",
                payment_method="Bank Transfer",
                notes="Reference number not found in bank records. Please resubmit with correct transaction ID.",
                verified_by=verifier,
                date_verified=now - timedelta(days=random.randint(1, 15)),
            )

        # Old verified payments for past-allocation students (2023/2024)
        past_students = [male_students[6], female_students[6]]
        for i, student in enumerate(past_students, start=300):
            Payment.objects.create(
                user=student,
                amount=Decimal("750000"),
                reference_number=_ref("TXN2324", i),
                status="verified",
                academic_year="2023/2024",
                payment_method="Bank Transfer",
                notes="Previous academic year payment - verified.",
                verified_by=verifier,
                date_verified=now - timedelta(days=220),
            )

        total = Payment.objects.count()
        verified = Payment.objects.filter(status="verified").count()
        pending = Payment.objects.filter(status="pending").count()
        rejected = Payment.objects.filter(status="rejected").count()
        self.stdout.write(self.style.SUCCESS(
            f"  OK {total} payments  ({verified} verified, {pending} pending, {rejected} rejected)"
        ))

    # -----------------------------------------------------------------------
    # Booking requests
    # -----------------------------------------------------------------------

    def _create_booking_requests(self, hostels, male_students, female_students, reviewer):
        """
        5 booking requests from unallocated students (indices 9):
          - 2 pending
          - 2 approved
          - 1 rejected
        """
        nsibirwa = hostels["Nsibirwa Hall"]
        mary_stuart = hostels["Mary Stuart Hall"]
        mitchell = hostels["Mitchell Hall"]

        requests_data = [
            # (student, hostel, message, status, admin_notes)
            (
                male_students[9],
                nsibirwa,
                "I am a final-year student and require a quiet single room close to the library.",
                "pending",
                None,
            ),
            (
                female_students[9],
                mary_stuart,
                "Requesting accommodation for Semester 2. I have a medical condition that requires ground-floor access.",
                "pending",
                None,
            ),
            (
                male_students[5],
                mitchell,
                "International exchange student - requesting postgraduate block.",
                "approved",
                "Approved. Room allocated separately.",
            ),
            (
                female_students[5],
                mitchell,
                "Postgraduate student - need quiet environment for research work.",
                "approved",
                "Approved. Please collect room key from the admin office.",
            ),
            (
                male_students[3],
                nsibirwa,
                "Requesting room transfer due to noise issues in current block.",
                "rejected",
                "No available rooms in requested block. Current allocation remains active.",
            ),
        ]

        for student, hostel, message, status, admin_notes in requests_data:
            BookingRequest.objects.create(
                student=student,
                preferred_hostel=hostel,
                academic_year="2024/2025",
                message=message,
                status=status,
                reviewed_by=reviewer if status in ("approved", "rejected") else None,
                admin_notes=admin_notes,
            )

        total = BookingRequest.objects.count()
        self.stdout.write(self.style.SUCCESS(f"  OK {total} booking requests"))

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    def _print_summary(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seed complete ===\n"))
        self.stdout.write("  Hostels   : " + str(Hostel.objects.count()))
        self.stdout.write("  Blocks    : " + str(Block.objects.count()))
        self.stdout.write("  Rooms     : " + str(Room.objects.count()))
        self.stdout.write("  Students  : " + str(User.objects.filter(is_student=True).count()))
        self.stdout.write("  Managers  : " + str(User.objects.filter(is_manager=True).count()))
        self.stdout.write("  Allocations : " + str(Allocation.objects.count()))
        self.stdout.write("  Payments  : " + str(Payment.objects.count()))
        self.stdout.write("  Booking requests : " + str(BookingRequest.objects.count()))
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n  Login credentials\n"
            "  -----------------\n"
            "  Managers (password: manager@2025)\n"
            "    warden_male    - Ssemakula Patrick\n"
            "    warden_female  - Namutebi Agnes\n"
            "\n"
            "  Students (password: student@2025)\n"
            "    Male  : mukasa_john, kato_brian, lubega_peter, nsubuga_paul,\n"
            "            wasswa_eman, mawejje_rob, kabugo_fran, ssenabulya_t,\n"
            "            mutebi_col, ssali_dan\n"
            "    Female: nakato_sarah, namutebi_gra, namukasa_joy, apio_susan,\n"
            "            akello_mary, nabakooza_p, nassali_ann, nankya_fat,\n"
            "            nakirya_dor, mutesi_vio\n"
        ))
