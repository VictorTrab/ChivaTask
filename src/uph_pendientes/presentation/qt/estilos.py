"""Hoja de estilos Qt compartida por la presentacion."""

STYLESHEET = """
QMainWindow, QWidget {
    background: #F5F7FA;
    color: #102033;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
#sidebar {
    background: #123F35;
    color: white;
}
#sidebar QLabel {
    background: transparent;
}
#sidebarMuted {
    color: rgba(255,255,255,0.35);
    font-size: 11px;
    padding: 8px;
}
#brand, #brandText {
    color: white;
    background: transparent;
    font-size: 20px;
    font-weight: 800;
}
#brandTextHeader {
    color: #102033;
    background: transparent;
    font-size: 23px;
    font-weight: 800;
}
#navItem, #navHint {
    color: rgba(255,255,255,0.68);
    padding: 10px 12px;
    background: transparent;
    border: none;
    text-align: left;
    border-radius: 10px;
    font-weight: 600;
}
#navHint {
    color: rgba(255,255,255,0.42);
    border: 1px solid rgba(255,255,255,0.10);
    margin-top: 8px;
}
#navItem:hover, #navHint:hover {
    background: rgba(255,255,255,0.08);
    color: white;
}
#navItemActive {
    background: #16775F;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 12px;
    text-align: left;
    font-weight: 700;
}
#title {
    font-size: 17px;
    font-weight: 800;
    color: #102033;
}
#subtitle, #muted {
    color: #64748B;
    font-size: 12px;
}
#sectionTitle {
    color: #102033;
    font-size: 14px;
    font-weight: 800;
}
#heroTitle {
    color: #102033;
    font-size: 22px;
    font-weight: 900;
}
#flatScroll {
    background: transparent;
    border: none;
}
#nextDeadlineCard {
    background: #ECFDF5;
    border: 1px solid #6EE7B7;
    border-radius: 14px;
}
#nextDeadlineText {
    color: #064E3B;
    font-size: 14px;
    font-weight: 800;
}
#footer {
    background: #FFFFFF;
    border-top: 1px solid #D8E2EA;
}
#errorBanner {
    background: #FEF2F2;
    border-top: 1px solid #FECACA;
    border-bottom: 1px solid #FECACA;
    color: #DC2626;
}
#statusOk, #statusPending, #statusSyncing, #statusError {
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 700;
    max-width: 240px;
}
#statusOk {
    background: #F0FBF5;
    color: #16775F;
    border: 1px solid #A7E3C0;
}
#statusPending, #statusSyncing {
    background: #EFF6FF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
}
#statusError {
    background: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
}
#statCard-default, #statCard-warning, #statCard-ok {
    background: white;
    border: 1px solid #D8E2EA;
    border-radius: 12px;
    font-weight: 600;
}
#statCard-warning {
    border-left: 3px solid #D97706;
}
#statIcon {
    background: #E9F7F1;
    border-radius: 10px;
    padding: 8px;
}
#statValue {
    color: #102033;
    font-size: 24px;
    font-weight: 800;
}
#statLabel {
    color: #64748B;
    font-size: 12px;
    font-weight: 600;
}
#metricCard-default, #metricCard-warning, #metricCard-danger, #metricCard-info, #metricCard-ok {
    background: #FFFFFF;
    border: 1px solid #D8E2EA;
    border-radius: 14px;
}
#metricIcon-default, #metricIcon-warning, #metricIcon-danger, #metricIcon-info, #metricIcon-ok {
    border-radius: 12px;
    padding: 9px;
}
#metricIcon-warning { background: #FEF3C7; }
#metricIcon-danger { background: #FEE2E2; }
#metricIcon-info { background: #DBEAFE; }
#metricIcon-ok { background: #D1FAE5; }
#metricValue {
    color: #102033;
    font-size: 24px;
    font-weight: 900;
}
#metricLabel {
    color: #53657F;
    font-size: 12px;
    font-weight: 600;
}
#detailPanel, #settingsCard {
    background: white;
    border: 1px solid #D8E2EA;
    border-radius: 12px;
}
#settingsCard {
    padding: 14px;
}
QTableWidget, #dataTable, #dataTree, QTreeWidget, QListWidget {
    background: white;
    border: 1px solid #D8E2EA;
    border-radius: 12px;
    gridline-color: #EEF3F7;
    selection-background-color: #E9F7F1;
    selection-color: #102033;
}
QTreeWidget::item, QListWidget::item {
    padding: 8px;
    border-radius: 8px;
}
QTreeWidget::item:selected, QListWidget::item:selected {
    background: #E8F5F0;
    color: #102033;
}
#taskGroup {
    background: #FFFFFF;
    border: 1px solid #D8E2EA;
    border-radius: 14px;
}
#taskGroupHeader {
    background: #F8FAFC;
    color: #102033;
    font-weight: 900;
    padding: 10px 14px;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}
#taskRow-overdue, #taskRow-pending, #taskRow-undated, #taskRow-ok {
    background: #FFFFFF;
    border-top: 1px solid #EEF3F7;
}
#taskRow-overdue:hover, #taskRow-pending:hover, #taskRow-undated:hover {
    background: #F8FAFC;
}
#taskRowTitle {
    color: #102033;
    font-size: 14px;
    font-weight: 800;
}
#taskRowMeta, #taskRowDate {
    color: #64748B;
    font-size: 12px;
}
#taskDot-overdue, #taskRelative-overdue { color: #D97706; font-weight: 800; }
#taskDot-pending, #taskRelative-pending { color: #16775F; font-weight: 800; }
#taskDot-undated, #taskRelative-undated { color: #2563EB; font-weight: 800; }
#taskDot-ok, #taskRelative-ok { color: #16A34A; font-weight: 800; }
#taskDot-overdue { background: #D97706; border-radius: 4px; }
#taskDot-pending { background: #16775F; border-radius: 4px; }
#taskDot-undated { background: #2563EB; border-radius: 4px; }
#taskDot-ok { background: #16A34A; border-radius: 4px; }
#courseCard {
    background: #FFFFFF;
    border: 1px solid #D8E2EA;
    border-radius: 14px;
}
#courseCard:hover {
    border: 1px solid #16775F;
    background: #FCFFFD;
}
#courseInitials {
    background: #D1FAE5;
    color: #16775F;
    border-radius: 22px;
    font-weight: 900;
}
#courseCode, #courseMeta {
    color: #8A9AB3;
    font-size: 12px;
    font-weight: 700;
}
#courseName {
    color: #102033;
    font-size: 14px;
    font-weight: 900;
}
#courseProgress, #ringBar {
    border: none;
    background: #EEF3F7;
    border-radius: 4px;
    height: 8px;
}
#courseProgress::chunk, #ringBar::chunk {
    background: #16775F;
    border-radius: 4px;
}
#primarySmallButton, #secondarySmallButton {
    border-radius: 9px;
    padding: 7px 11px;
    font-weight: 800;
}
#primarySmallButton {
    background: #16775F;
    color: #FFFFFF;
    border: none;
}
#secondarySmallButton {
    background: #FFFFFF;
    color: #102033;
    border: 1px solid #D8E2EA;
}
#emptyState {
    background: #FFFFFF;
    border: 1px dashed #D8E2EA;
    border-radius: 14px;
}
#emptyTitle {
    color: #64748B;
    font-size: 14px;
    font-weight: 800;
}
#emptySubtitle {
    color: #94A3B8;
    font-size: 12px;
}
#settingsRow {
    background: #FFFFFF;
    border: 1px solid #E8EEF4;
    border-radius: 12px;
}
#settingsRowTitle {
    color: #102033;
    font-size: 14px;
    font-weight: 800;
}
#settingsRowSubtitle {
    color: #53657F;
    font-size: 12px;
}
#toggleOn, #toggleOff {
    border: none;
    border-radius: 14px;
    font-size: 9px;
    font-weight: 900;
}
#toggleOn {
    background: #16775F;
    color: #FFFFFF;
    text-align: right;
}
#toggleOff {
    background: #CBD5E1;
    color: #FFFFFF;
    text-align: left;
}
#pillFilter {
    background: transparent;
    border: none;
}
#pill, #pillActive {
    border-radius: 18px;
    padding: 8px 14px;
    font-weight: 800;
}
#pill {
    background: #FFFFFF;
    color: #53657F;
    border: 1px solid #D8E2EA;
}
#pill:hover {
    background: #F8FAFC;
    color: #102033;
}
#pillActive {
    background: #E8F5F0;
    color: #047857;
    border: 1px solid #B7E4D4;
}
#segmentedControl {
    background: #FFFFFF;
    border: 1px solid #D8E2EA;
    border-radius: 10px;
}
#segment, #segmentActive {
    border: none;
    padding: 8px 14px;
    font-weight: 800;
}
#segment {
    background: transparent;
    color: #64748B;
}
#segmentActive {
    background: #16775F;
    color: #FFFFFF;
    border-radius: 8px;
}
#progressRing, #miniCalendar {
    background: #FFFFFF;
    border: 1px solid #D8E2EA;
    border-radius: 14px;
}
#progressRingValue {
    color: #102033;
    font-size: 24px;
    font-weight: 900;
}
#progressRingLabel, #calendarDow {
    color: #8A9AB3;
    font-size: 12px;
    font-weight: 700;
}
#calendarTitle {
    color: #102033;
    font-size: 14px;
    font-weight: 900;
}
#calendarDay, #calendarToday, #calendarMark-overdue, #calendarMark-pending {
    border-radius: 12px;
}
#calendarToday {
    background: #D1FAE5;
    color: #065F46;
    font-weight: 900;
}
#calendarMark-overdue {
    background: #FEF3C7;
    color: #B45309;
    font-weight: 900;
}
#calendarMark-pending {
    background: #E8F5F0;
    color: #16775F;
    font-weight: 900;
}
QHeaderView::section {
    background: #EEF3F7;
    padding: 9px;
    border: none;
    font-weight: 700;
}
#settingsNav {
    background: #F8FAFC;
    border: 1px solid #D8E2EA;
    border-radius: 12px;
    padding: 6px;
}
#settingsNav::item {
    padding: 10px;
    border-radius: 8px;
    color: #64748B;
}
#settingsNav::item:selected {
    background: #E8F5F0;
    color: #16775F;
    font-weight: 700;
}
#detailTitle {
    font-size: 18px;
    font-weight: 800;
    color: #102033;
}
#primaryButton, #dangerPrimaryButton {
    background: #16775F;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 800;
}
#primaryButton:hover {
    background: #0F5F4A;
}
#dangerPrimaryButton {
    background: #DC2626;
}
#dangerPrimaryButton:hover {
    background: #B91C1C;
}
#secondaryButton {
    background: #FFFFFF;
    color: #102033;
    border: 1px solid #D8E2EA;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 700;
}
#secondaryButton:hover {
    background: #F8FAFC;
}
#dangerButton {
    background: #FFF5F5;
    color: #DC2626;
    border: 1px solid #FECACA;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 700;
}
#dangerButton:hover {
    background: #FEE2E2;
}
#linkButton {
    background: transparent;
    border: none;
    color: #DC2626;
    text-decoration: underline;
    font-weight: 800;
}
#iconButton {
    background: white;
    border: 1px solid #D8E2EA;
    border-radius: 20px;
}
#iconButton:hover {
    background: #E9F7F1;
}
QLineEdit, QComboBox {
    background: white;
    border: 1px solid #D8E2EA;
    border-radius: 10px;
    padding: 9px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #16775F;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    height: 0px;
}
QCheckBox {
    color: #102033;
    spacing: 8px;
}
#chip-overdue, #chip-undated, #chip-pending, #chip-ok, #chip-error, #chip-neutral {
    border-radius: 13px;
    padding: 4px 10px;
    font-weight: 800;
}
#chip-overdue {
    background: #FEF3C7;
    color: #92400E;
}
#chip-undated {
    background: #DBEAFE;
    color: #1D4ED8;
}
#chip-pending {
    background: #E8F5F0;
    color: #16775F;
}
#chip-ok {
    background: #DCFCE7;
    color: #166534;
}
#chip-error {
    background: #FEE2E2;
    color: #991B1B;
}
#chip-neutral {
    background: #F1F5F9;
    color: #475569;
}
#baseModal {
    background: #FFFFFF;
    border-radius: 16px;
}
"""
