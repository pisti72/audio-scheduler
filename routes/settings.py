@app.route('/settings')
@login_required
def settings():
    current_lang = session.get('lang', 'en')
    translations = TRANSLATIONS[current_lang]
    return render_template('settings.html', 
                         translations=translations,
                         current_lang=current_lang)

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    new_username = data.get('newUsername')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    # Verify current password
    if not check_credentials(session.get('username'), current_password):
        return jsonify({'success': False, 'error': 'Invalid current password'})

    # Update credentials
    try:
        set_credentials(new_username, new_password if new_password else current_password)
        return jsonify({
            'success': True, 
            'requireRelogin': True if new_username != session.get('username') else False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})