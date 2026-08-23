"""Initial database schema with partial unique index for active slots

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('PATIENT', 'DOCTOR', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Doctor Profiles table
    op.create_table(
        'doctor_profiles',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('specialisation', sa.String(255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Doctor Working Hours table
    op.create_table(
        'doctor_working_hours',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('doctor_id', sa.CHAR(36), sa.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
    )

    # 4. Doctor Leaves table
    op.create_table(
        'doctor_leaves',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('doctor_id', sa.CHAR(36), sa.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leave_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('doctor_id', 'leave_date', name='uq_doctor_leave_date'),
    )

    # 5. Appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('doctor_id', sa.CHAR(36), sa.ForeignKey('doctor_profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('patient_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('appointment_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('status', sa.Enum('HELD', 'BOOKED', 'COMPLETED', 'CANCELLED_BY_PATIENT', 'CANCELLED_BY_LEAVE', name='appointmentstatus'), nullable=False),
        sa.Column('hold_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('symptoms', sa.Text(), nullable=True),
        sa.Column('pre_visit_summary', sa.Text(), nullable=True),
        sa.Column('pre_visit_summary_status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='aisummarystatus'), nullable=False, server_default='PENDING'),
        sa.Column('pre_visit_summary_error', sa.Text(), nullable=True),
        sa.Column('urgency', sa.Enum('Low', 'Medium', 'High', name='urgencylevel'), nullable=True),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('suggested_questions', sa.JSON(), nullable=True),
        sa.Column('doctor_notes', sa.Text(), nullable=True),
        sa.Column('prescription', sa.Text(), nullable=True),
        sa.Column('post_visit_summary', sa.JSON(), nullable=True),
        sa.Column('post_visit_summary_status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='aisummarystatus'), nullable=False, server_default='PENDING'),
        sa.Column('post_visit_summary_error', sa.Text(), nullable=True),
        sa.Column('patient_calendar_event_id', sa.String(255), nullable=True),
        sa.Column('doctor_calendar_event_id', sa.String(255), nullable=True),
        sa.Column('patient_calendar_sync_status', sa.Enum('NONE', 'PENDING', 'SYNCED', 'FAILED', name='calendarsyncstatus'), nullable=False, server_default='NONE'),
        sa.Column('doctor_calendar_sync_status', sa.Enum('NONE', 'PENDING', 'SYNCED', 'FAILED', name='calendarsyncstatus'), nullable=False, server_default='NONE'),
        sa.Column('overall_calendar_sync_status', sa.Enum('NOT_CONNECTED', 'PENDING', 'PARTIAL', 'SYNCED', 'FAILED', name='overallcalendarsyncstatus'), nullable=False, server_default='NOT_CONNECTED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Partial Unique Index on Appointments for Concurrency Slot Protection
    op.create_index(
        'uq_doctor_active_slot',
        'appointments',
        ['doctor_id', 'appointment_date', 'start_time'],
        unique=True,
        postgresql_where=sa.text("status IN ('HELD', 'BOOKED')"),
        sqlite_where=sa.text("status IN ('HELD', 'BOOKED')")
    )

    # 6. Notification Logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('idempotency_key', sa.String(255), nullable=False, unique=True),
        sa.Column('appointment_id', sa.CHAR(36), sa.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('notification_type', sa.Enum('BOOKING_CONFIRMATION', 'APPOINTMENT_REMINDER', 'CANCELLATION', 'LEAVE_CONFLICT', 'MEDICATION_REMINDER', name='notificationtype'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', name='notificationstatus'), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 7. Medication Reminders table
    op.create_table(
        'medication_reminders',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('appointment_id', sa.CHAR(36), sa.ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('medication_name', sa.String(255), nullable=False),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'COMPLETED', name='reminderstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Calendar Connections table
    op.create_table(
        'calendar_connections',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('provider', sa.String(50), nullable=False, server_default='google'),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('calendar_connections')
    op.drop_table('medication_reminders')
    op.drop_table('notification_logs')
    op.drop_index('uq_doctor_active_slot', table_name='appointments')
    op.drop_table('appointments')
    op.drop_table('doctor_leaves')
    op.drop_table('doctor_working_hours')
    op.drop_table('doctor_profiles')
    op.drop_table('users')
