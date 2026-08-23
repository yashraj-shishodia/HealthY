/**
 * Helper utility to format doctor names cleanly without duplicate "Dr. Dr." prefixes.
 */
export const formatDoctorName = (name?: string): string => {
  if (!name) return 'Dr. Specialist';
  const trimmed = name.trim();
  if (/^dr\./i.test(trimmed)) {
    return trimmed;
  }
  return `Dr. ${trimmed}`;
};
