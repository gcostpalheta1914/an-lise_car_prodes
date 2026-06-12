# ... dentro do if not st.session_state.logado:
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Debug: Isso vai mostrar o que está sendo digitado na tela
        st.write(f"Você digitou: Usuário='{usuario}', Senha='{senha}'")
        
        if usuario == "gabriel" and senha == "Gab1914.":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Credenciais não conferem com: 'gabriel' e 'Gab1914.'")
